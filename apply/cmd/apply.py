from __future__ import print_function
import argparse
import collections
import sys, os

import llnl.util.tty as tty
import llnl.util.filesystem as fs
import ruamel

import spack
import spack.cmd
import spack.environment as ev
import spack.util.spack_yaml as syaml
import spack.build_environment as build_environment
from spack.error import SpackError


description = (
    "install and make available as custom modules a description of an environment"
)
section = "apply"
level = "long"


def setup_parser(subparser):
    subparser.add_argument(
        "--install",
        default=os.environ.get("SPACK_APPLY_INSTALL_PATH", None),
        type=str,
        help="where to put the install tree",
    )
    subparser.add_argument(
        "--modules",
        default=os.environ.get("SPACK_APPLY_MODULEFILES_PATH", None),
        type=str,
        help="where to put the tree of modulefiles",
    )
    subparser.add_argument(
        "--tag",
        type=str,
        default=[],
        action='append',
        help='only build modules with these tags'
    )
    subparser.add_argument(
        "configs",
        nargs=argparse.REMAINDER,
        type=argparse.FileType("r"),
        help="config files to be read",
    )


def apply(parser, args):
    class Module:
        def __init__(self, name, specs, **kwargs):
            self.name, self.specs = (name, specs)
            self.attrs = kwargs
            self.prefix = fs.join_path(args.install, self.name)
            self.env_file = fs.join_path(self.prefix, "spack.yaml")
            self.module_file = fs.join_path(args.modules, self.name)

            self._env = None

        def __getattr__(self, attr):
            return self.attrs[attr]

        @property
        def env(self):
            if not self._env:
                self._env = ev.get_env(
                    collections.namedtuple("Fakeargs", "env")(env=self.prefix),
                    "apply",
                    required=True,
                )
            return self._env

        def env_defn(self):
            yaml_dict = {}
            yaml_dict["view"] = fs.join_path(args.install, self.name)
            yaml_dict["concretization"] = self.concretization
            yaml_spec_list = yaml_dict.setdefault("specs", [])
            yaml_spec_list[:] = [str(s) for s in self.specs]

            return {"spack": yaml_dict}

        def module_defn(self):
            env = spack.util.environment.inspect_path(
                self.prefix,
                spack.config.get("modules:prefix_inspections", {}),
                exclude=spack.util.environment.is_system_path,
            )
            _ = spack.util.environment.EnvironmentModifications()

            for spec in self.env._get_environment_specs():
                build_environment.set_module_variables_for_package(spec.package)
                spec.package.setup_build_environment(env)
                spec.package.setup_run_environment(env)

            for k, v in self.variables.items():
                env.set(k, v)

            module_commands = {
                "SetEnv": lambda i: ("setenv", i.name, '"%s"'%i.value) if i.value else ("",)*3,
                "UnsetEnv": lambda i: ("unsetenv", i.name, ""),
                "AppendPath": lambda i: ("append-path", i.name, i.value),
                "PrependPath": lambda i: ("prepend-path", i.name, i.value),
                "RemovePath": lambda i: ("remove-path", i.name, i.value),
            }

            modulefile = ["#%Module -*- tcl -*-"]
            modulefile += [
                '{} {: >30} {}'.format(*module_commands[type(i).__name__](i))
                for i in env if type(i).__name__ in module_commands
            ]
            if self.whatis:
                modulefile.append('module-whatis "%s"' % str(self.whatis))
            return "\n".join(modulefile)

    modules = [
        Module(
            m["name"],
            [s for spec in m["specs"] for s in spack.cmd.parse_specs(spec)],
            variables=m.get("variables", {}),
            whatis=m.get("whatis", ""),
            write_modulefile=m.get("write_modulefile", True),
            concretization=m.get("concretization", "together"),
            tag=m.get("tag", "")
        )
        for c in args.configs
        for m in syaml.load(c)
    ]

    for m in modules:
        if args.tag and m.tag not in args.tag:
            continue
        if m.tag and m.tag not in args.tag:
            continue

        tty.msg("Building module %s" % m.name)

        fs.mkdirp(fs.ancestor(m.env_file))
        with fs.write_tmp_and_move(m.env_file) as f:
            ruamel.yaml.dump(m.env_defn(), f)

        cs = m.env.concretize(force=True)
        ev.display_specs(cs)
        m.env.install_all()

        tty.msg("Updating view at %s" % m.prefix)
        m.env.regenerate_views()

        if m.write_modulefile:
            tty.msg("Writing modulefile at %s" % m.module_file)

            fs.mkdirp(fs.ancestor(m.module_file))
            with fs.write_tmp_and_move(m.module_file) as f:
                f.write(m.module_defn())

        print()

    tty.msg("Done!")
