FROM nvidia/cuda:11.0.3-cudnn8-devel-ubuntu18.04

ARG PORT=8081
ENV PORT=${PORT}

RUN apt-get update && apt-get install -y \
    wget \
    tar \
    python3 \
    python3-pip \
    sox

ENV HOME=/app
WORKDIR $HOME
COPY . .

RUN pip3 install -r requirements.txt
ENV PYTHONPATH $PYTHONPATH:main

CMD python3 main/server.py --port=$PORT --external_scorer_path=$EXTERNAL_SCORER_PATH --scorer_alpha=$SCORER_ALPHA --scorer_beta=$SCORER_BETA