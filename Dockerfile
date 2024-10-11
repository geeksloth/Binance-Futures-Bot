FROM python:3.9.18
ENV PYTHON_TA_LIB_PACKAGE_NAME "TA-lib"
ENV PYTHON_TA_LIB_VERSION "0.4.28"

RUN apt-get -y update
RUN python3 -m pip install --upgrade pip
RUN pip3 install numpy
RUN pip3 install requests
RUN pip3 install setuptools
RUN cd /tmp
RUN curl -L -O http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
	&& tar -xzf ta-lib-0.4.0-src.tar.gz \
	&& cd ta-lib/ \
	&& sed -i 's/^#define TA_IS_ZERO(v).*$/#define TA_IS_ZERO(v) (((-0.000000000000000001)<v)\&\&(v<0.000000000000000001))/' src/ta_func/ta_utility.h \
	&& sed -i 's/^#define TA_IS_ZERO_OR_NEG(v).*$/#define TA_IS_ZERO_OR_NEG(v) (v<0.000000000000000001)/' src/ta_func/ta_utility.h \
	&& ./configure --prefix=/usr \
	&& make \
	&& make install \
    && pip3 install ${PYTHON_TA_LIB_PACKAGE_NAME}==${PYTHON_TA_LIB_VERSION}
WORKDIR /app/binancesloth
RUN pip3 install python-binance
RUN pip3 install binance-future
RUN pip3 install binance-futures-connector
RUN pip3 install tabulate