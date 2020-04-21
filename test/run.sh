#!/bin/bash -l
set -euo pipefail

tests=$(realpath $(dirname $0))/modules
install=$(realpath ./install)
modules=$(realpath ./modulefiles)

spack apply --install $install --modules $modules $tests/zlib.yaml

module use $modules
module avail
module whatis zlib/1

module load zlib/1
find $CPATH -name zlib.h -exec ls -l {} \;

module swap zlib zlib/2
find $CPATH -name zlib.h -exec ls -l {} \;

module unload zlib/2

echo building default modules
spack apply --install $install --modules $modules $tests/tags.yaml
module show zlib/untagged
! module show zlib/cpu
! module show zlib/gpu

echo building cpu modules
spack apply --tag cpu --install $install --modules $modules $tests/tags.yaml
module show zlib/untagged
module show zlib/cpu
! module show zlib/gpu

echo building gpu modules
spack apply --tag gpu --install $install --modules $modules $tests/tags.yaml
module show zlib/untagged
module show zlib/cpu
module show zlib/gpu
