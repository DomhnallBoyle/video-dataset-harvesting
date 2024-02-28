FROM ubuntu:18.04

ARG PORT=8080
ENV PORT=${PORT}

# core dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3 \
    python3-pip \
    git

ENV HOME=/app
WORKDIR $HOME
COPY . .

RUN pip3 install -r requirements.txt
ENV PYTHONPATH=$PYTHONPATH:main
ENV ENVIRONMENT=production

CMD python3 main/server.py --port=$PORT