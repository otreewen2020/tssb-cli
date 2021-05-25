"""
Usage:

  run_tssb_script.py <script> [options]

Options:
  -h  --help    Help screen
  -d  --debug   Sets log level to DEBUG
"""

import logging
import sys
import os
import time
from os.path import dirname, basename
from subprocess import run

from pywinauto.application import Application
from pywinauto.keyboard import send_keys


log = logging.getLogger(__name__)

# Keeping the path short speeds up execution: we are sending in less keystrokes
TSSB_WORKDIR = "c:\\t"

SLEEP_STEP = 0.05
TIMEOUT = 60
MARKER_TEXT = "TSSB_CLI_END_MARKER"


def main(tssb_script):
    if not tssb_script.startswith(TSSB_WORKDIR):
        raise ValueError(f"Script should be under {TSSB_WORKDIR}")

    script_with_marker = f'{TSSB_WORKDIR}\\s.scr'
    if tssb_script == script_with_marker:
        raise ValueError(f"Conflict: cannot use {tssb_script} as path")

    # Copy over the script to temp file and add finish marker
    with open(script_with_marker, 'w') as f_out:
        with open(tssb_script, 'r') as f_in:
            for line in f_in:
                f_out.write(line)
        f_out.write(f'\n\nREAD {MARKER_TEXT};\n')

    os.chdir(TSSB_WORKDIR)

    app = Application(backend="win32").start('C:\\tssb\\tssb.exe')

    log.info(f'Started TSSB')

    timer = TIMEOUT
    while timer:
        try:
            if len(app.windows(title=u'Disclaimer of Liability')) > 0:
                break
        except:
            time.sleep(SLEEP_STEP)
            timer -= SLEEP_STEP
    else:
        raise ValueError("TSSB did not start in time")

    # Send enter to accept the 'Disclaimer of Liability' form
    send_keys('{ENTER}')

    log.debug(f'Accepted disclaimer: {app.windows()} / {app.windows()[0].children()}')

    # Wait for main window to activate
    timer = TIMEOUT
    while timer:
        try:
            if app.windows(title_re='TSSB.*') and len(app.windows()[0].children()) == 1:
                break
        except:
            pass

        time.sleep(SLEEP_STEP)
        timer -= SLEEP_STEP
    else:
        log.error("Timeout while waiting for disclaimer window to disappear")
        raise ValueError("Error accepting disclaimer")

    # Open 'File -> Script file to read'
    # NOTE: with wine menu select is not working, hence the keystrokes
    send_keys('{VK_MENU}{ENTER}{ENTER}')

    log.debug(f'Open in progress: {app.windows()} / {app.windows()[0].children()}')

    timer = TIMEOUT
    while timer:
        try:
            if len(app.windows(title=u'Script file to read')) > 0:
                break
        except:
            time.sleep(SLEEP_STEP)
            timer -= SLEEP_STEP
    else:
        raise ValueError("Script file to read dialog did not appear")

    log.info(f"Starting script `{script_with_marker}`")
    send_keys(script_with_marker + '{ENTER}')

    # Wait for processing to start
    while len(app.windows(title=u'Script file to read')) > 0:
        time.sleep(SLEEP_STEP)

    log.debug(f"Waiting to finish: {app.windows()} / {app.windows()[0].children()}")

    # Wait for processing to finish
    error_dialogs_found = 0
    while True:
        try:
            dialogs = str(app.windows()[0].children())
        except Exception:
            # Sometimes the window handle goes out of context before we reach children(), hence we ignore that exception
            continue

        if MARKER_TEXT in dialogs:
            error_dialogs_found = 0
            log.debug("Success!")
            break

        if 'ButtonWrapper' in dialogs:
            # It could happen that we load the dialog during it is filled, thus the MARKER_TEXT is not yet visible.
            # Doing a double-check (hopefully) resolves the problem.
            error_dialogs_found += 1
            if error_dialogs_found == 2:
                log.error(f'Error while processing: {dialogs} / {app.windows()} / {app.windows()[0].children()}')
                raise ValueError(f'Error while processing: {dialogs} / {app.windows()} / {app.windows()[0].children()}')

        time.sleep(SLEEP_STEP * 2)

    log.info("TSSB Script completed")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        exit(1)

    tssb_script = sys.argv[1]
    if not os.path.exists(tssb_script):
        raise ValueError(f'TSSB Script does not exists: {tssb_script}')

    log_level = logging.INFO

    for option in sys.argv[2:]:
        if option in ('-d', '--debug'):
            log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    main(tssb_script)
