"""
Usage:
  tssb <script> <job_name> <description> [options]

Options:
  -d  --debug              Set log level to DEBUG
  --data-dir=DIR           Sets the data dir to be mounted as c:\\tssb-data. [default: parse-from-script]
  --work-dir=DIR           Sets the work dir (which serves as result dir as well), where the script will run.
                           If set to 'script-dir' dir is generated in the scripts dir [default: script-dir]
  --x11=DISPLAY            Use the defined display as output [default: off]
  --disable-screenshots    Disables the regular screenshots taken from TSSB window
"""
from typing import List, Set, Optional, Tuple, Dict, Any
from os import makedirs
from os.path import basename, dirname, abspath
from copy import copy
from shutil import copy as copy_file
from datetime import datetime
from multiprocessing import Pool
from functools import partial
import sys
import os

import logging

from docopt import docopt
from subprocess_tee import run as shell_run


log = logging.getLogger(__name__)

TSSB_WORKDIR_UNIX = '$HOME/.wine/drive_c/t'
TSSB_WORKDIR_WIN = 'c:\\\\t'

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


def prepare_workdir(
        job_name: str, script: List[str], script_path: str,
        data_dir: str, work_dir: str,
        dependencies: Set[str]) -> Tuple[str, str]:
    tssb_data_win_path = "c:\\tssb-data"

    if work_dir == 'script-dir':
        work_dir = f'{dirname(script_path)}/tssb.{job_name}'
        log.info(f"Workdir: {work_dir}")
    makedirs(work_dir, exist_ok=True)

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
        if data_dir == 'parse-from-script':
            raise ValueError("data-dir not found")

    log.info(f"Data dir set to: {data_dir}")

    modified_script = replace_market_histories_in_script(script, data_dir=tssb_data_win_path)

    script_in_work_dir = f'{work_dir}/{basename(script_path)}'
    with open(script_in_work_dir, 'w') as f:
        f.writelines(modified_script)

    for filename in dependencies:
        filepath = ''
        if not filename.startswith('/'):
            filepath = f'{dirname(script_path)}'
        copy_file(f'{filepath}/{filename}', f'{work_dir}/{filename}')

    return work_dir, data_dir


def run(workdir_path: str, script_filename: str, data_dir: str,
        job_name: str, description: str,
        x11_display: Optional[str], disable_screenshots: bool):
    log_filename = f'{workdir_path}/tssb-cli.log'
    x11_args = ''
    start_cmd = '/xvfb-run-with-screenshots.sh wine'
    if x11_display:
        x11_args = (
            f'export DISPLAY={x11_display}; '
            f'export NO_XVFB=true; '
        )
        start_cmd = 'wine'

    disable_screenshot_args = ''
    if disable_screenshots:
        disable_screenshot_args = 'export SCREENSHOTS="";'

    link_tssb_data = f'ln -sf {abspath(data_dir)} $HOME/.wine/drive_c/tssb-data; '
    unlink_tssb_data = f'unlink $HOME/.wine/drive_c/tssb-data; '
    link_tssb_workdir = f'ln -sf {abspath(workdir_path)} {TSSB_WORKDIR_UNIX}; '
    unlink_tssb_workdir = f'unlink {TSSB_WORKDIR_UNIX}; '

    cmd = (
        f'set -xo pipefail; '
        f'echo "{job_name}: {description}\nStart: $(date)" >> {log_filename}; '
        f'{x11_args} '
        f'{disable_screenshot_args} '
        f'{link_tssb_data} '
        f'{link_tssb_workdir} '
        f'date; '
        f'time {start_cmd} C:\\\\Python38\\\\python.exe C:\\\\tssb\\\\run_tssb_script.py {TSSB_WORKDIR_WIN}\\\\{script_filename} | tee -a {log_filename} 2>&1; '
        f'date; '
        f'{unlink_tssb_workdir} '
        f'{unlink_tssb_data} '
        f'echo "Finish: $(date)" >> {log_filename}; '
    )

    log.info(f'Starting TSSB: {cmd}')
    # WORKAROUND: 'executable' kwarg of shell_run is not respected in subprocess_tee.
    # The default /bin/sh errors due to `set -o pipefail`
    os.environ['SHELL'] = '/bin/bash'
    shell_run(cmd, echo=True, check=True, shell=True)
    log.info(f'TSSB finished')


def prepare_and_run(opts: Dict[str, Any], script: List[str], dependencies: Set[str]) -> str:
    script_path = opts['<script>']
    script_filename = basename(script_path)

    now = datetime.now().strftime('%y%m%d_%H%M%S')
    script_name_sanitized = basename(script_path).replace('.scr', '')
    job_name = f'{now}-{script_name_sanitized}-{opts["<job_name>"]}'

    x11_display = None
    if opts['--x11'] != 'off':
        x11_display = opts['--x11']

    work_dir, data_dir = prepare_workdir(
        job_name, script, script_path, opts['--data-dir'], opts['--work-dir'], dependencies)

    run(work_dir, script_filename,
        data_dir, job_name, opts['<description>'],
        x11_display, opts['--disable-screenshots'])

    return work_dir


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

    work_dir = prepare_and_run(opts, script, dependencies)
    log.info(f'TSSB Results: {work_dir}')


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    main()
