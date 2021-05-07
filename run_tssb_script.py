import sys
import pywinauto
from pywinauto.application import Application
from pywinauto.keyboard import send_keys

TSSB_SCRIPT = sys.argv[1]

SLEEP_STEP = 0.05
TIMEOUT = 60

app = Application(backend="win32").start('C:\\tssb\\tssb.exe')

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

# Open 'File -> Script file to read'
# NOTE: with wine menu select is not working, hence the keystrokes
send_keys('{VK_MENU}{ENTER}{ENTER}')

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
