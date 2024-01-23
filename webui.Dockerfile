#FROM python:3.10-alpine
#LABEL maintainer="kunyuan"
#ENV LC_ALL=C.UTF-8
#ENV LANG=C.UTF-8
#ENV TZ=Asia/Shanghai
#RUN apk update && \
#    apk add tzdata --no-cache && \
#    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
#    apk del tzdata && \
#    mkdir -p /usr/share/zoneinfo/Asia/ && \
#    ln -s /etc/localtime /usr/share/zoneinfo/Asia/Shanghai
#
#COPY . /home/openai-forward
#WORKDIR /home/openai-forward
#RUN apk add patch g++ gcc libstdc++ leveldb-dev linux-headers cmake make --no-cache && \
#    pip install -e .[webui] --no-cache-dir && \
#    pip install streamlit --no-cache-dir --no-deps && \
#    pip install "lmdb>=1.4.1" "plyvel>=1.5.0" --no-cache-dir && \
#    apk del g++ gcc cmake make && rm -rf /var/cache/apk/*


FROM python:3.10

LABEL maintainer="kunyuan"

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV TZ=Asia/Shanghai

RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /home/openai-forward

WORKDIR /home/openai-forward

RUN apt-get update && \
    apt-get install -y patch g++ gcc libstdc++6 libtcmalloc-minimal4 libleveldb-dev cmake make build-essential && \
    pip install -e .[webui] --no-cache-dir && \
    pip install "lmdb>=1.4.1" "plyvel>=1.5.0" --no-cache-dir && \
    apt-get remove -y patch g++ gcc cmake make && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


EXPOSE 8000
ENTRYPOINT ["python", "-m", "openai_forward.__main__", "run", "--webui", "true"]
