FROM nvidia/cuda:11.0.3-cudnn8-devel-ubuntu18.04

ARG PORT=8084
ENV PORT=${PORT}

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    python3 \
    python3-pip \
    wget

ENV HOME=/app
WORKDIR $HOME
COPY . .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
ENV PYTHONPATH=$PYTHONPATH:main

# RUN ./download_model.sh
RUN mkdir -p /var/www/data

CMD python3 main/server.py --port=$PORT