FROM registry.kelly.direct/tssb-cli:base-1.94

ENV SCREENSHOTS="/root/.wine/drive_c/t/"
ENV SCREENSHOTS_DELAY="1800"
ENV SCREENSHOTS_INITIAL_DELAY="600"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      python3-pip \
      scrot && \
    rm -rf /var/lib/apt/lists/*
    
ADD docker/xvfb-run-with-screenshots.sh /
ADD wine/run_tssb_script.py /root/.wine/drive_c/tssb/

ADD setup.py /src/
ADD build_cli.sh /src/
ADD tssb_cli /src/tssb_cli
RUN \
  cd /src/ && \
  mkdir bin && \
  ./build_cli.sh && \
  mv bin/tssb_cli /usr/bin/tssb_cli

ENTRYPOINT [ "/usr/bin/tssb_cli" ]
