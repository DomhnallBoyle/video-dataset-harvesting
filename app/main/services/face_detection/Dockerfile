FROM nvidia/cuda:10.2-cudnn7-devel-ubuntu18.04

ARG PORT=8083
ENV PORT=${PORT}

RUN apt-get update && apt-get install -y \
    cmake \
    python3 \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    libopenblas-dev \
    liblapack-dev

ENV HOME=/app
WORKDIR $HOME
COPY . .


# # OPENFACE INSTALL INSTRUCTIONS
# RUN apt-get install -y \
#     git \
#     libgtk2.0-dev \
#     pkg-config \
#     libavcodec-dev \
#     libavformat-dev \
#     libswscale-dev \
#     python-dev \
#     python-numpy \
#     libtbb2 \
#     libtbb-dev \
#     libjpeg-dev \
#     libpng-dev \
#     libtiff-dev \
#     libdc1394-22-dev \
#     wget \
#     unzip \
#     libboost-all-dev \
#     g++-8
# # install opencv
# WORKDIR /opt
# RUN wget https://github.com/opencv/opencv/archive/4.1.0.zip && unzip 4.1.0.zip
# RUN mkdir opencv-4.1.0/build
# WORKDIR /opt/opencv-4.1.0/build
# RUN cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D BUILD_TIFF=ON -D WITH_TBB=ON ..
# RUN make -j2
# RUN make install
# # install dlib
# WORKDIR /opt
# RUN wget http://dlib.net/files/dlib-19.22.tar.bz2 && tar -xvf dlib-19.22.tar.bz2
# RUN mkdir dlib-19.22/build
# WORKDIR /opt/dlib-19.22/build
# RUN cmake .. -DCMAKE_CXX_FLAGS="-fPIC"
# RUN cmake --build . --config Release
# RUN make install
# RUN ldconfig
# # install OpenFace
# WORKDIR /opt
# RUN git clone https://github.com/a-hurst/OpenFace.git
# RUN mkdir OpenFace/build
# WORKDIR /opt/OpenFace/build
# RUN cmake -D CMAKE_CXX_COMPILER=g++-8 -D CMAKE_C_COMPILER=gcc-8 -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_CXX_FLAGS="-fPIC" ..
# RUN make -j2
# RUN ldconfig
# # install OpenFace python bindings
# WORKDIR /opt/OpenFace
# RUN git checkout pybind11
# WORKDIR /opt/OpenFace/python_api
# RUN python3 setup.py install


RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
ENV PYTHONPATH=$PYTHONPATH:main

CMD python3 main/server.py --port=$PORT