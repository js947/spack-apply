#!/bin/bash
set -euo pipefail

ROOT=$(realpath $(dirname $0))
cd $ROOT

SPACK=$(mktemp -d)
trap "rm -rf $SPACK" EXIT

git clone --depth=1 https://github.com/spack/spack $SPACK
source $SPACK/share/spack/setup-env.sh

INSTALL=$(mktemp -d)
MODULES=$(mktemp -d)
trap "rm -rf $SPACK $INSTALL $MODULES" EXIT

ln -sf $(realpath config/config.yaml) $(which spack | xargs dirname | xargs dirname)/etc/spack
spack apply --install $INSTALL --modules $MODULES modules/zlib.yaml

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