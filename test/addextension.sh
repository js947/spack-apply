#!/bin/bash -l
set -euo pipefail

python test/addextension.py \
  $(spack config --scope site edit config --print-file) \
  $(pwd)
