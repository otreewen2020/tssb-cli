import sys
import os
import time
from os.path import dirname
import pywinauto
from pywinauto.application import Application
from pywinauto.keyboard import send_keys

TSSB_SCRIPT = sys.argv[1]

SLEEP_STEP = 0.05
TIMEOUT = 60

os.chdir(dirname(TSSB_SCRIPT))
app = Application(backend="win32").start('C:\\tssb\\tssb.exe')

print(f'Started: {app.windows()[0].children()}')

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

print(f'Accepted disclaimer: {app.windows()[0].children()}')

# Wait for main window to activate
timer = TIMEOUT
while timer:
    try:
        if app.windows(title_re = 'TSSB.*'):
            break
    except:
        time.sleep(SLEEP_STEP)
        timer -= SLEEP_STEP
else:
    raise ValueError("Error accepting disclaimer")

print(f'Opening script: {app.windows()[0].children()}')

# Open 'File -> Script file to read'
# NOTE: with wine menu select is not working, hence the keystrokes
send_keys('{VK_MENU}{ENTER}{ENTER}')

print(f'Open in progress: {app.windows()[0].children()}')

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

print(f"Starting script: {TSSB_SCRIPT}")
send_keys(TSSB_SCRIPT + '{ENTER}')

# Wait for processing to start
while len(app.windows()[0].children()) == 1:
    time.sleep(SLEEP_STEP)

# In case of failure a new dialog comes up with okay button.
# Hence finding ButtonWrapper in the children shows failure.
error_dialog_ok_buttons = [e for e in app.windows()[0].children() if 'ButtonWrapper' in str(type(e))]
if error_dialog_ok_buttons:
    raise ValueError(f'Error while processing: {app.windows()[0].children()}')

# Wait for processing to finish
while len(app.windows()[0].children()) != 1:
    time.sleep(SLEEP_STEP * 2)

print("TSSB Script Done")
