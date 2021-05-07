# tssb-cli
Welcome to hell: run TSSB from CLI, using WINE, Docker and PyWinAuto

## Preparing base docker image:
The [docker-wine](https://github.com/scottyhardy/docker-wine) image was taken as base.
Given that python installer requires X/UI running, the installation process is done manually:
  1. Create wine-docker container:
     ```
     git clone https://github.com/tibkiss/docker-wine
     cd docker-wine
     docker build --network=host --build-arg TAG=ubuntu-20.04 --build-arg WINE_BRANCH=devel -t docker-wine .
     ```
  2. Start the container:
     ```
     docker run \
         --rm \
	 --network=host \
         --name tssb-install \
	 -it \
	 --env="RUN_AS_ROOT=yes" \
	 --env="DISPLAY" \
	 --volume="${XAUTHORITY:-${HOME}/.Xauthority}:/root/.Xauthority:ro" \
	 --volume="/tmp/.X11-unix:/tmp/.X11-unix:ro" \
	 docker-wine /bin/bash
     ```
  3. Install python (inside container):
     ```
     cd /root
     wget https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe
     wine python-3.8.10-amd64.exe
     ```
     *Note: Sometimes the screen comes up scrambled. Restart the installer in that case :)*

     __Customize installation:__ 
      - 'Documentation', 'tcl/tk and IDLE' and 'Python test suite' is not required
      - Install for all users to custom location: `C:\Python38`

     Cleanup:
     ```
     rm python-3.8.10-amd64.exe
     ```

  4. Install and patch PyWinAuto (inside container):
     ```
     wine /root/.wine/drive_c/Python38/python.exe -m pip install PyWinAuto==0.6.8
     ```

     Given that the current wine version (5.0.1) does not include UIAutomation.dll the following manual [patch](https://github.com/robertschulze/pywinauto/pull/1/files) should be applied to PyWinAuto:
     ```
     wget -O /root/.wine/drive_c/Python38/Lib/site-packages/pywinauto/sysinfo.py https://raw.githubusercontent.com/robertschulze/pywinauto/add4e852d4f34093e6f3f4ba780c5d718057a1e6/pywinauto/sysinfo.py
     ```

  5. Download tssb and dependencies (inside container):
     ```
     mkdir /root/.wine/drive_c/tssb/
     wget -O /root/.wine/drive_c/tssb/tssb.exe http://tssbsoftware.com/downloads/TSSB.exe
     wget -O /root/.wine/drive_c/tssb/cudart64_80.dll http://tssbsoftware.com/downloads/cudart64_80.dll
     ```

  6. Validate installation (inside container)
     Start python: 
     ```
     wine /root/.wine/drive_c/Python38/python.exe
     ```
     And use the following script to start notepad:
     ```
     from pywinauto.application import Application
     from pywinauto.keyboard import SendKeys

     app = Application(backend="win32").start('c:\\tssb\\tssb.exe')
     SendKeys('{ENTER}')
     ```

  7. Install vim
     ```
     apt install --no-install-recommends -y vim-tiny
     ```

  8. Snapshot and upload image (from host):
     ```
     docker commit tssb-install registry.kelly.direct/tssb-cli:base-1.94
     docker push registry.kelly.direct/tssb-cli:base-1.94
     ```




