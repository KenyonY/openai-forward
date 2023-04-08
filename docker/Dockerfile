FROM beidongjiedeguang/ubuntu:22.04
LABEL maintainer="placeholer"
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
WORKDIR /home
RUN ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
COPY . /home/openai-forward
WORKDIR /home/openai-forward
RUN pip install -e . --no-cache-dir && mv openai_forward .. && rm -rf /home/openai-forward/* && mv ../openai_forward .

ENTRYPOINT ["openai_forward", "run"]