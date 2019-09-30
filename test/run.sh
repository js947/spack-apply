#!/bin/bash
set -euo pipefail

ROOT=$(realpath $(dirname $0))
cd $ROOT

SPACK_DIR=$(mktemp -d)
trap "rm -rf $SPACK_DIR" exit

git clone https://github.com/spack/spack $SPACK_DIR
SPACK=$SPACK_DIR/bin/spack

$SPACK -C ./config apply --install ./tmp/install --modules ./tmp/modules modules/*

unset MODULEPATH
module use ./tmp/modules
module avail
module whatis zlib/1

module load zlib/1
find $CPATH -name zlib.h -exec ls -l {} \;

module swap zlib zlib/2
find $CPATH -name zlib.h -exec ls -l {} \;

module unload zlib/2
