from __future__ import print_function
import argparse
import collections
import sys, os

import llnl.util.tty as tty
import llnl.util.filesystem as filesystem

import spack
import spack.cmd
import spack.util.spack_yaml as syaml
from spack.error import SpackError
from spack.filesystem_view import YamlFilesystemView

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
        default="./modulefiles",
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
                for s in spack.cmd.parse_specs(spec, concretize=True)
            ],
        )
        for c in args.configs
        for m in syaml.load(c)
    ]

    for m in modules:
        tty.msg("Building module %s" % m.name)

        for s in [s for s in m.specs if not s.package.installed]:
            s.package.do_install()

        prefix = filesystem.join_path(args.install, m.name)
        view = YamlFilesystemView(
            prefix,
            spack.store.layout,
            ignore_conflicts=True,
            link=os.symlink,
            verbose=args.verbose,
        )
        view.remove_specs(
            *(set(view.get_all_specs()) - set(m.specs)), with_dependencies=False
        )
        view.add_specs(
            *(set(m.specs) - set(view.get_all_specs())), with_dependencies=False
        )
        view.print_status(*m.specs)

        modulefile = ["#%Module -*- tcl -*-"]
        modulefile += [
            "prepend_path {: >30} {}".format(i.name, os.path.realpath(i.value))
            for i in spack.util.environment.inspect_path(
                prefix,
                spack.config.get("modules:prefix_inspections", {}),
                exclude=spack.util.environment.is_system_path,
            )
        ]
        modulefile_path = filesystem.join_path(args.modules, m.name)

        tty.msg("Writing modulefile at %s" % modulefile_path)
        filesystem.mkdirp(filesystem.ancestor(modulefile_path))
        with open(modulefile_path, "w") as f:
            f.write('\n'.join(modulefile))
