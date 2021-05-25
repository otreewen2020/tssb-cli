#!/bin/bash -x

set -eEuo pipefail

if [ -e tssb ]; then
  rm -f tssb
fi

INTERPRETER=$(which python3)

${INTERPRETER} -m pip install . --target tssb_cli_build
mv tssb_cli_build/tssb_cli/__main__.py tssb_cli_build/
rm -rf tssb_cli_build/bin tssb_cli_build/*.dist-info tssb_cli_build/__pycache__
${INTERPRETER} -m zipapp -p "/usr/bin/env ${INTERPRETER}" tssb_cli_build

rm -rf tssb_cli_build
mv tssb_cli_build.pyz bin/tssb_cli
