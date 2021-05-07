FROM registry.kelly.direct/tssb-cli:base-1.94

ADD run_tssb_script.py /root/.wine/drive_c/tssb/
ADD entrypoint.sh /
ENTRYPOINT [ "/entrypoint.sh" ]
