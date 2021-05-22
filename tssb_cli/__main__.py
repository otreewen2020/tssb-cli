"""
Usage:
  tssb <script> <job_name> <description> [options]

Options:
  -d  --debug                 Set log level to DEBUG
  --data-dir=DIR              Sets the data dir to be mounted as c:\\tssb-data. [default: parse-from-script]
  --docker-img=IMG            Sets the docker image to use [default: registry.kelly.direct/tssb-cli:latest]
  --x11=DISPLAY               Use the defined display as output [default: off]
  --disable-screenshots       Disables the regular screenshots taken from TSSB window
  --parallel-by-var=PROC_CNT  Run the specified script in parallel by dividing the job based on variables [default: off]
"""
from typing import List, Set, Optional, Tuple, Dict, Any
from os import makedirs
from os.path import basename, dirname, abspath
from copy import copy
from shutil import copy as copy_file
from datetime import datetime
from multiprocessing import Pool
from functools import partial
import json
import sys

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


def replace_market_histories_in_script(script: List[str], data_dir: str) -> List[str]:
    modified_script = copy(script)
    for i, line in enumerate(script):
        if line.find("READ MARKET HISTORIES") != -1:
            splitted = line.split('"')
            filepath = splitted[1]
            if filepath.startswith(data_dir):
                # Already in right format, no need to modify
                break
            modified_filepath = f'{data_dir}\\{basename(filepath)}'
            splitted[1] = modified_filepath
            modified_line = '"'.join(splitted)
            modified_script[i] = modified_line
            break
    return modified_script


def prepare_workdir(job_name: str, script: List[str], script_path: str, data_dir: str,
                    dependencies: Set[str], parallel_jobs: int, instance: int) -> Tuple[str, str]:
    tssb_data_win_path = "c:\\tssb-data"
    workdir_path = f'job.{job_name}.{parallel_jobs}-{instance}'
    log.info(f"Workdir: {workdir_path}")
    makedirs(workdir_path)

    if data_dir == 'parse-from-script':
        log.info("Finding data dir in script")
        for line in script:
            if line.find("READ MARKET HISTORIES") != -1:
                market_histories_file = line.split('"')[1]
                if market_histories_file.lower().startswith(tssb_data_win_path):
                    raise ValueError("Market History is windows path, please specify data-dir")
                data_dir = dirname(market_histories_file)
                if not data_dir.startswith('/'):
                    log.info(f'{script_path}: {abspath(dirname(script_path))}')
                    data_dir = abspath(dirname(script_path)) + f'/{data_dir}'
                break

    log.info(f"Data dir set to: {data_dir}")

    modified_script = replace_market_histories_in_script(script, data_dir=tssb_data_win_path)

    script_in_workdir = f'{workdir_path}/{basename(script_path)}'
    with open(script_in_workdir, 'w') as f:
        f.writelines(modified_script)

    for file in dependencies:
        copy_file(file, f'{workdir_path}/{file}')

    if parallel_jobs != 1:
        var_filename = [e for e in dependencies if e.find('.var') != -1][0]

        shell_run(f'split -n l/{parallel_jobs} -d {workdir_path}/{var_filename} {workdir_path}/VAR', echo=True, check=True)
        shell_run(f'rm {workdir_path}/{var_filename}', echo=True, check=True)
        shell_run(f'mv {workdir_path}/VAR{instance:02} {workdir_path}/{var_filename}', echo=True, check=True)

    return workdir_path, data_dir


def run(workdir_path: str, script_filename: str, data_dir: str, docker_img: str, job_name: str, description: str,
        x11_display: Optional[str], disable_screenshots: bool):
    log_filename = f'{workdir_path}/tssb-cli.log'
    shell_run(f'echo "{job_name}: {description}\nStart: $(date)" >> {log_filename}')
    x11_args = ''
    if x11_display:
        x11_args = (
            f'-e DISPLAY={x11_display} '
            f'-e NO_XVFB=true '
            f'-v $HOME/.Xauthority:/root/.Xauthority:ro '
            f'-v /tmp/.X11-unix:/tmp/.X11-unix:ro '
        )
    disable_screenshot_args = ''
    if disable_screenshots:
        disable_screenshot_args = ' -e SCREENSHOTS="" '

    cmd = (
        f'(time docker run '
        f'  -it --rm  '
        f'  {x11_args} '
        f'  {disable_screenshot_args} '
        f'  -v {abspath(data_dir)}:/root/.wine/drive_c/tssb-data:ro '
        f'  -v {abspath(workdir_path)}:/root/.wine/drive_c/tssb-workdir '
        f'  {docker_img} c:\\\\tssb-workdir\\\\{script_filename} ) | tee -a {log_filename} 2>&1  '
    )

    log.info(f'Starting tssb: {cmd}')
    shell_run(cmd, echo=True, check=True)

    shell_run(f'echo "Finish: $(date)" >> {log_filename}')


def prepare_and_run(opts: Dict[str, Any], script: List[str], dependencies: List[str],
                    parallel_jobs: int, instance: int):
    script_path = opts['<script>']
    script_filename = basename(script_path)

    now = datetime.now().strftime('%y%m%d_%H%M%S')
    job_name = f'{now}-{opts["<job_name>"]}'

    x11_display = None
    if opts['--x11'] != 'off':
        x11_display = opts['--x11']

    workdir_path, data_dir = prepare_workdir(job_name, script, script_path, opts['--data-dir'],
                                             dependencies, parallel_jobs, instance)
    run(workdir_path, script_filename,
        data_dir, opts['--docker-img'],
        job_name, opts['<description>'],
        x11_display, opts['--disable-screenshots'])

    return workdir_path


def main():
    opts = docopt(__doc__)
    print(opts)

    if opts['-d']:
        log.setLevel(logging.DEBUG)

    script_path = opts['<script>']

    with open(script_path) as f:
        script = f.readlines()

    dependencies = get_dependencies(script)
    # _ = get_write_targets(script)

    parallel_jobs = 1
    with Pool(processes=parallel_jobs) as pool:
        workdirs = pool.map(partial(prepare_and_run, opts, script, dependencies, parallel_jobs), range(parallel_jobs))

    log.info(f'TSSB Results: {json.dumps(workdirs)}')


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    main()
