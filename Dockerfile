FROM ubuntu:latest
RUN apt-get update
RUN apt-get install -y \
    python3 \
    python3-pip
RUN python3 -m pip install --upgrade pip
WORKDIR /bot
COPY ta-lib-0.4.0-src.tar.gz /bot/
RUN tar -xzf ta-lib-0.4.0-src.tar.gz
WORKDIR /bot/ta-lib
RUN ./configure
RUN make
RUN make install
RUN python3 -m pip install \
    ta-lib
RUN python3 -m pip install \
    colorama
WORKDIR /bot
RUN python3 -m pip install \
    requests 
RUN python3 -m pip install \
#    python-binance \
#    binance-future \
    binance-futures-connector
RUN apt-get install iputils-ping