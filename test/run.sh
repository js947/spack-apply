#!/bin/bash
set -euo pipefail

ROOT=$(realpath $(dirname $0))
SPACK=$ROOT/../spack/bin/spack
cd $ROOT

$SPACK -C ./config apply --install ./tmp/install --modules ./tmp/modules modules/*

unset MODULEPATH
module use ./tmp/modules
module avail
module whatis zlib/1

module load zlib/1
find $CPATH -name zlib.h

module swap zlib zlib/2
find $CPATH -name zlib.h

module unload zlib/2
