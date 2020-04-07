#!/bin/bash
set -euo pipefail

spack apply --install ./install --modules ./modulefiles modules/zlib.yaml

module use $MODULES
module avail
module whatis zlib/1

module load zlib/1
find $CPATH -name zlib.h -exec ls -l {} \;

module swap zlib zlib/2
find $CPATH -name zlib.h -exec ls -l {} \;

module unload zlib/2

echo building default modules
spack apply --install $INSTALL --modules $MODULES modules/tags.yaml
module show zlib/untagged
! module show zlib/cpu
! module show zlib/gpu

echo building cpu modules
spack apply --tag cpu --install $INSTALL --modules $MODULES modules/tags.yaml
module show zlib/untagged
module show zlib/cpu
! module show zlib/gpu

echo building gpu modules
spack apply --tag gpu --install $INSTALL --modules $MODULES modules/tags.yaml
module show zlib/untagged
module show zlib/cpu
module show zlib/gpu
