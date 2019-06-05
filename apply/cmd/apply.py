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
from spack.error import SpackError

description = (
    "install and make available as custom modules a description of an environment"
)
section = "apply"
level = "long"


def setup_parser(subparser):
    subparser.add_argument(
        "--install", default="./install", type=str, help="where to put the install tree"
    )
    subparser.add_argument(
        "--modules",
        default="./install/modulefiles",
        type=str,
        help="where to put the tree of modulefiles",
    )
    subparser.add_argument(
        "configs",
        nargs=argparse.REMAINDER,
        type=argparse.FileType("r"),
        help="config files to be read",
    )


def apply(parser, args):
    class Module:
        def __init__(self, name, specs):
            self.name, self.specs = name, specs
            self.prefix = fs.join_path(args.install, self.name)
            self.env_file = fs.join_path(self.prefix, "spack.yaml")
            self.module_file = fs.join_path(args.modules, self.name)

            self.env = ev.get_env(
                collections.namedtuple("Fakeargs", "env")(env=self.prefix),
                "apply",
                required=True,
            )

        @property
        def env_defn(self):
            yaml_dict = {}
            yaml_dict["view"] = fs.join_path(args.install, self.name)
            yaml_spec_list = yaml_dict.setdefault("specs", [])
            yaml_spec_list[:] = [str(s) for s in self.specs]

            return {"spack": yaml_dict}

        @property
        def module_defn(self):
            env = spack.util.environment.inspect_path(
                self.prefix,
                spack.config.get("modules:prefix_inspections", {}),
                exclude=spack.util.environment.is_system_path,
            )
            _ = spack.util.environment.EnvironmentModifications()

            for spec in self.env._get_environment_specs():
                spec.package.setup_environment(_, env)

            modulefile = ["#%Module -*- tcl -*-"]
            modulefile += [
                "{} {: >30} {}".format(
                    {
                        "SetEnv": "setenv",
                        "UnSetEnv": "unsetenv",
                        "AppendPath": "append-path",
                        "PrependPath": "prepend-path",
                        "RemovePath": "remove-path",
                    }[type(i).__name__],
                    i.name,
                    os.path.realpath(i.value),
                )
                for i in env
            ]
            return "\n".join(modulefile)

    modules = [
        Module(
            m["name"],
            [s for spec in m["packages"] for s in spack.cmd.parse_specs(spec)],
        )
        for c in args.configs
        for m in syaml.load(c)
    ]

    for m in modules:
        tty.msg("Building module %s at %s" % (m.name, m.prefix))

        fs.mkdirp(fs.ancestor(m.env_file))
        with open(m.env_file, "w") as f:
            ruamel.yaml.dump(m.env_defn, f)

        m.env.concretize(force=True)
        m.env.install_all()

        tty.msg("Writing modulefile at %s" % m.module_file)

        fs.mkdirp(fs.ancestor(m.module_file))
        with open(m.module_file, "w") as f:
            f.write(m.module_defn)

        print()

    tty.msg("Done!")
