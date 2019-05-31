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
    Module = collections.namedtuple("Module", "name,specs")
    modules = [
        Module(
            m["name"],
            [
                s
                for spec in m["packages"]
                for s in spack.cmd.parse_specs(spec)
            ],
        )
        for c in args.configs
        for m in syaml.load(c)
    ]

    for m in modules:
        prefix = fs.join_path(args.install, m.name)
        tty.msg("Building module %s at %s" % (m.name, prefix))

        yaml_dict = {}
        yaml_dict['view'] = fs.join_path(args.install, m.name)
        yaml_spec_list = yaml_dict.setdefault('specs', [])
        yaml_spec_list[:] = [str(s) for s in m.specs]

        fs.mkdirp(prefix)
        with fs.write_tmp_and_move(fs.join_path(prefix, "spack.yaml")) as f:
            ruamel.yaml.dump({'spack': yaml_dict}, f)

        env = ev.get_env(
            collections.namedtuple("Fakeargs", "env")(env=prefix),
            "apply",
            required=True,
        )
        env.concretize(force=True)
        env.install_all()

        modulefile = ["#%Module -*- tcl -*-"]
        modulefile += [
            "prepend-path {: >30} {}".format(i.name, os.path.realpath(i.value))
            for i in spack.util.environment.inspect_path(
                prefix,
                spack.config.get("modules:prefix_inspections", {}),
                exclude=spack.util.environment.is_system_path,
            )
        ]
        modulefile_path = fs.join_path(args.modules, m.name)

        tty.msg("Writing modulefile at %s" % modulefile_path)
        fs.mkdirp(fs.ancestor(modulefile_path))
        with fs.write_tmp_and_move(modulefile_path) as f:
            f.write("\n".join(modulefile))

        print()

    tty.msg("Done!")
