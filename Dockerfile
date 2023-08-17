FROM python:3.10-alpine
LABEL maintainer="kunyuan"
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV TZ=Asia/Shanghai
RUN apk update && \
    apk add tzdata --no-cache && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    apk del tzdata && \
    mkdir -p /usr/share/zoneinfo/Asia/ && \
    ln -s /etc/localtime /usr/share/zoneinfo/Asia/Shanghai

COPY . /home/openai-forward
WORKDIR /home/openai-forward
RUN pip install -e . --no-cache-dir

EXPOSE 8000
ENTRYPOINT ["python", "-m", "openai_forward.__main__", "run"]
