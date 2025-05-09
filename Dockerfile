FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y python3-opencv libgl1 libglib2.0-0

CMD ["/bin/bash"] # Or whatever command you want to run when the container starts
