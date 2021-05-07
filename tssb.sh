#!/bin/bash

set -eEuo pipefail

script=$(realpath ${1})
script_dir=$(dirname ${script})

IMG=registry.kelly.direct/tssb-cli:latest
DATA_DIR=/mnt/wd6/tssb-daily-csvs

docker run \
    -it \
    --rm \
    -v ${DATA_DIR}:/root/.wine/drive_c/tssb-data/:ro \
    -v ${script_dir}:/root/.wine/drive_c/tssb-scripts/ \
    ${IMG} c:\\tssb-scripts\\$(basename ${script})
