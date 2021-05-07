#!/bin/bash -x

set -eEuo pipefail

set +u
XVFB=xvfb-run
if [ ! -z "${NO_XVFB}" ]; then
  XVFB=""
fi
set -u

${XVFB} wine C:\\Python38\\python.exe C:\\tssb\\run_tssb_script.py $*
