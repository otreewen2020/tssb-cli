"""
Usage:
  tssb <script> <job_name> <description> [options]

Options:
  -d  --debug       Set log level to DEBUG
  --data-dir=DIR    Sets the data dir to be mounted as c:\\tssb-data [default: /mnt/wd6/tssb-daily-csvs]
  --docker-img=IMG  Sets the docker image to use [default: registry.kelly.direct/tssb-cli:latest]
"""
from typing import List, Set
from os import makedirs
from os.path import basename, abspath
from shutil import copy
from datetime import datetime

import logging

from docopt import docopt
from subprocess_tee import run as shell_run


log = logging.getLogger(__name__)


def get_dependencies(script: List[str]) -> Set[str]:
    """Returns resources referenced by the script"""
    resources = set()
    for line in script:
        # NOTE: READ MARKET HISTORIES is ignored to avoid moving historical data
        if line.strip().startswith(('READ MARKET LIST', 'READ VARIABLE LIST', 'READ DATABASE', 'APPEND DATABASE')):
            filename = line.split('"')[1]
            resources.add(filename)
    log.debug(f"Dependencies: {resources}")
    return resources


def get_write_targets(script: List[str]) -> Set[str]:
    write_targets = set()
    for line in script:
        if line.strip().startswith('WRITE DATABASE'):
            filename = line.split('"')[1]
            write_targets.add(filename)
    log.debug(f"Write targets: {write_targets}")
    return write_targets


def prepare_workdir(job_name: str, script_path: str, dependencies: Set[str]) -> str:
    workdir_path = f'job.{job_name}'
    log.info(f"Workdir: {workdir_path}")
    makedirs(workdir_path)

    copy(script_path, f'{workdir_path}/{basename(script_path)}')

    for file in dependencies:
        copy(file, f'{workdir_path}/{file}')

    return workdir_path


def run(workdir_path: str, script_filename: str, data_dir: str, docker_img: str, job_name: str, description: str):
    log_filename = f'{workdir_path}/tssb-cli.log'
    shell_run(f'echo "{job_name}: {description}\nStart: $(date)" >> {log_filename}')
    cmd = (
        f'(time docker run '
        f'  -it --rm  '
        f'  -v {abspath(data_dir)}:/root/.wine/drive_c/tssb-data:ro '
        f'  -v {abspath(workdir_path)}:/root/.wine/drive_c/tssb-workdir '
        f'  {docker_img} c:\\\\tssb-workdir\\\\{script_filename} ) | tee -a {log_filename} 2>&1  | tr -d "\r"'
    )

    log.info(f'Starting tssb: {cmd}')
    shell_run(cmd, echo=True, check=True)

    shell_run(f'echo "Finish: $(date)" >> {log_filename}')


def main():
    opts = docopt(__doc__)
    print(opts)

    if opts['-d']:
        log.setLevel(logging.DEBUG)

    script_path = opts['<script>']

    with open(script_path) as f:
        script = f.readlines()

    now = datetime.now().strftime('%y%m%d_%H%M%S')
    job_name = f'{now}-{opts["<job_name>"]}'
    dependencies = get_dependencies(script)
    _ = get_write_targets(script)

    workdir_path = prepare_workdir(job_name, script_path, dependencies)
    script_filename = basename(script_path)
    run(workdir_path, script_filename, opts['--data-dir'], opts['--docker-img'], job_name, opts['<description>'])
    log.info(f'TSSB Results: {workdir_path}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    main()
