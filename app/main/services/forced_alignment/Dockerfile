FROM ubuntu:18.04

ARG PORT=8082
ENV PORT=${PORT}

# core dependencies
RUN apt-get update && apt-get install -y \
    sox \
    gcc-multilib \
    python3 \
    python3-dev \
    python3-pip \
    git \
    vim \
    wget \
    curl \
    tar \
    zip

ENV HOME=/app
WORKDIR $HOME
COPY . .

# install HTK 3.4
RUN tar -xvf htk.tar.gz
WORKDIR $HOME/htk
ENV CPPFLAGS -UPHNALG
RUN ./configure --disable-hlmtools --disable-hslab
RUN make -j4 all
RUN make -j4 install

# install python dependencies
WORKDIR $HOME
RUN pip3 install -r requirements.txt
ENV PYTHONPATH=$PYTHONPATH:main

CMD python3 main/server.py --port=$PORT