import sys
import os
import time
from os.path import dirname, basename
import pywinauto
from pywinauto.application import Application
from pywinauto.keyboard import send_keys

TSSB_SCRIPT = sys.argv[1]
TSSB_CLI_TEMP = "C:\\tssb-cli-temp"

SLEEP_STEP = 0.05
TIMEOUT = 60

os.chdir(dirname(TSSB_SCRIPT))

# Copy over the script to \temp and add finish marker
MARKER_TEXT="TSSB_CLI_END_MARKER"
script_with_marker = f'{TSSB_CLI_TEMP}\\{basename(TSSB_SCRIPT)}'
os.mkdir(TSSB_CLI_TEMP)
with open(script_with_marker, 'w') as f_out:
    with open(TSSB_SCRIPT, 'r') as f_in:
        for line in f_in:
            f_out.write(line)
    f_out.write(f'\n\nREAD {MARKER_TEXT};\n')
    

app = Application(backend="win32").start('C:\\tssb\\tssb.exe')

print(f'[DEBUG] Started: {app.windows()} / {app.windows()[0].children()}')

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

print(f'[DEBUG] Accepted disclaimer: {app.windows()} / {app.windows()[0].children()}')

# Wait for main window to activate
timer = TIMEOUT
while timer:
    try:
        if app.windows(title_re = 'TSSB.*') and len(app.windows()[0].children()) == 1:
            break
    except:
        time.sleep(SLEEP_STEP)
        timer -= SLEEP_STEP
else:
    raise ValueError("Error accepting disclaimer")

print(f'[DEBUG] Opening script: {app.windows()} / {app.windows()[0].children()}')

# Open 'File -> Script file to read'
# NOTE: with wine menu select is not working, hence the keystrokes
send_keys('{VK_MENU}{ENTER}{ENTER}')

print(f'[DEBUG] Open in progress: {app.windows()} / {app.windows()[0].children()}')

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

print(f"[DEBUG] Starting script `{script_with_marker}`: {app.windows()} / {app.windows()[0].children()}")
send_keys(script_with_marker + '{ENTER}')

# Wait for processing to start
while len(app.windows(title=u'Script file to read')) > 0:
    time.sleep(SLEEP_STEP)

print(f"[DEBUG] Waiting to finish: {app.windows()} / {app.windows()[0].children()}")

# Wait for processing to finish
while True:
    # print(f"[DEBUG] {app.windows()} / {app.windows()[0].children()}")
    dialogs = app.windows()[0].children()
    if any(MARKER_TEXT in str(e) for e in dialogs):
        print("Success!")
        break

    # In case of failure a new dialog comes up with okay button.
    # Hence finding ButtonWrapper in the children shows failure.
    error_dialog_ok_buttons = [e for e in dialogs if 'ButtonWrapper' in str(type(e))]
    if error_dialog_ok_buttons:
        raise ValueError(f'Error while processing: {app.windows()} / {app.windows()[0].children()}')

    time.sleep(SLEEP_STEP * 2)

print("TSSB Script Done")
