FROM nvidia/cuda:11.0.3-cudnn8-devel-ubuntu18.04

ARG PORT=8086
ENV PORT=${PORT}

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    python3 \
    python3-pip

ENV HOME=/app
WORKDIR $HOME
COPY . .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
ENV PYTHONPATH=$PYTHONPATH:main

CMD python3 main/server.py --port=$PORT