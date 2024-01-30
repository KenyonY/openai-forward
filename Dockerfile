FROM python:3.10-slim
LABEL maintainer="K.Y"
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV TZ=Asia/Shanghai

RUN apt update && \
    apt install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /home/openai-forward
WORKDIR /home/openai-forward
RUN apt-get update && \
    apt-get install -y patch g++ gcc libstdc++6 libtcmalloc-minimal4 libleveldb-dev cmake make build-essential && \
    pip3 install -e . --no-cache-dir && \
    apt-get remove -y patch g++ gcc cmake make build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


EXPOSE 8000
ENTRYPOINT ["python3", "-m", "openai_forward.__main__", "run"]
