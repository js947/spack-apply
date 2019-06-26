#!/bin/bash
set -euo pipefail

ROOT=$(realpath $(dirname $0))
cd $ROOT
if which -s spack
then
  SPACK=spack
else
  SPACK=$ROOT/../spack/bin/spack
fi

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
