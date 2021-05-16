#!/bin/bash -x

set -eEuo pipefail

env | sort

set +u
XVFB=/xvfb-run-with-screenshots.sh
if [ ! -z "${NO_XVFB}" ]; then
  XVFB=""
fi
set -u

${XVFB} wine C:\\Python38\\python.exe C:\\tssb\\run_tssb_script.py $*
