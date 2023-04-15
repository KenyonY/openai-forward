FROM python:3.10-alpine
LABEL maintainer="kunyuan"
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN pip install --no-cache-dir  \
    "loguru" \
    "fastapi" \
    "uvicorn" \
    "orjson" \
    "python-dotenv" \
    "httpx"

WORKDIR /home
COPY . /home/openai-forward
WORKDIR /home/openai-forward

RUN pip install . --no-cache-dir && rm -rf /home/openai-forward/*
EXPOSE 8000
ENTRYPOINT ["openai_forward", "run"]
