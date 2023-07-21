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

RUN pip install --no-cache-dir  \
    "loguru" \
    "sparrow-python>=0.1.3" \
    "fastapi" \
    "uvicorn" \
    "orjson" \
    "python-dotenv" \
    "httpx" \
    "pytz"

COPY . /home/openai-forward
WORKDIR /home/openai-forward
ENV ssl_keyfile="/home/openai-forward/privkey.pem"
ENV ssl_certfile="/home/openai-forward/fullchain.pem"
EXPOSE 8000
ENTRYPOINT ["python", "-m", "openai_forward.__main__", "run"]
