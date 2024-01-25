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


EXPOSE 8000 8001
ENTRYPOINT ["python", "-m", "openai_forward.__main__", "run", "--webui"]
