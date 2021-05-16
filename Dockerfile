FROM registry.kelly.direct/tssb-cli:base-1.94

ENV SCREENSHOTS="/root/.wine/drive_c/tssb-workdir/"
ENV SCREENSHOTS_DELAY="1800"
ENV SCREENSHOTS_INITIAL_DELAY="600"

RUN apt update && \
    apt install -y --no-install-recommends scrot && \
    rm -rf /var/lib/apt/lists/*
    
ADD docker/entrypoint.sh docker/xvfb-run-with-screenshots.sh /
ADD wine/run_tssb_script.py /root/.wine/drive_c/tssb/

ENTRYPOINT [ "/entrypoint.sh" ]
