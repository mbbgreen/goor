FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y python3-opencv libgl1 libglib2.0-0 bash

CMD ["/bin/bash"]
