# tssb-cli
Welcome to the unofficial tssb-cli, which leverages WINE, Docker and PyWinAuto to run [TSSB](https://tssbsoftware.com) on Linux and OS X.

## Tutorial
Given that python installer requires X/UI running, majority of the installation process is done manually:
  1. Create wine-docker base container:
     ```
     docker build --network=host --build-arg WINE_BRANCH=devel -t docker-wine -f Dockerfile.base .
     ```

  2. Start the container:
     ```
     docker run \
         --rm \
         --network=host \
         --name tssb-install \
         -it \
         -v "${XAUTHORITY:-${HOME}/.Xauthority}:/root/.Xauthority:ro" \
	 -v "/tmp/.X11-unix:/tmp/.X11-unix:ro" \
	 docker-wine /bin/bash
     ```

  3. Install python (inside container):
     ```
     cd /root
     wget https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe
     export DISPLAY=<<DISPLAY_HERE>>
     wine python-3.8.10-amd64.exe
     rm python-3.8.10-amd64.exe
     ```
     *Note: Sometimes the screen comes up scrambled. Restart the installer in that case :)*

     __Customize installation:__ 
      - 'Documentation', 'tcl/tk and IDLE' and 'Python test suite' is not required
      - Install for all users to custom location: `C:\Python38`

  4. Install and patch PyWinAuto (inside container):
     ```
     wine /root/.wine/drive_c/Python38/python.exe -m pip install PyWinAuto==0.6.8
     ```

     Given that the current wine version (6.7) does not include UIAutomation.dll the following manual [patch](https://github.com/robertschulze/pywinauto/pull/1/files) should be applied to PyWinAuto:
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
     And use the following script to validate:
     ```
     from pywinauto.application import Application
     from pywinauto.keyboard import SendKeys

     app = Application(backend="win32").start('c:\\tssb\\tssb.exe')
     SendKeys('{ENTER}')
     ```

  7. Snapshot and upload image (from host):
     ```
     docker commit tssb-install my-registry/tssb-cli:base-1.94
     docker push my-registry/tssb-cli:base-1.94
     ```

  8. Build TSSB image:
     ```
     docker build -t my-registry/tssb-cli:latest .
     docker tag my-registry/tssb-cli:latest my-registry/tssb-cli:1.94
     ```

  9. Run:
     - Using the shell script:
       ```
       ./tssb.sh /home/tssb-user/tssb-scripts/find_groups.scr
       ```

     - Standalone using docker:
       ```
       docker run \
         --rm \
         --network=host \
         -it \
         -v /mnt/wd6/tssb-daily-csvs:/root/.wine/drive_c/tssb-data/:ro \
         -v /home/tssb-user/tssb-scripts:/root/.wine/drive_c/tssb-scripts/ \
         my-registry/tssb:latest c:\\tssb-scripts\\find_groups.scr
       ```
    
     - With X11 Forwarding:
       ```
       docker run \
         --network=host \
         -it \
         -e DISPLAY \
         -e NO_XVFB=true \
         -v "${XAUTHORITY:-${HOME}/.Xauthority}:/root/.Xauthority:ro" \
         -v "/tmp/.X11-unix:/tmp/.X11-unix:ro" \
         -v /mnt/wd6/tssb-daily-csvs:/root/.wine/drive_c/tssb-data/:ro \
         -v /home/tssb-user/tssb-scripts/:/root/.wine/drive_c/tssb-scripts/ \
         my-registry/tssb:latest c:\\tssb-scripts\\find_groups.scr
       ```

