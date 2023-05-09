**中文** | [**English**](./README_EN.md)

<h1 align="center">
    <br>
    OpenAI Forward
    <br>
</h1>
<p align="center">
    <b> OpenAI API 接口转发服务 <br/>
    The fastest way to deploy openai api forwarding </b>
</p>

<p align="center">
    <a href="https://pypi.org/project/openai-forward/"><img src="https://img.shields.io/pypi/v/openai-forward?color=brightgreen" alt="PyPI version" ></a>
    <a href="https://github.com/beidongjiedeguang/openai-forward/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/github/license/beidongjiedeguang/openai-forward.svg?color=blue&style=flat-square">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward/releases">
        <img alt="Release (latest by date)" src="https://img.shields.io/github/v/release/beidongjiedeguang/openai-forward">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward">
        <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/beidongjiedeguang/openai-forward">
    </a>
    <a href="https://hub.docker.com/r/beidongjiedeguang/openai-forward">
        <img alt="docer image size" src="https://img.shields.io/docker/image-size/beidongjiedeguang/openai-forward?style=flat&label=docker image">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward/actions/workflows/run_tests.yaml">
        <img alt="tests" src="https://img.shields.io/github/actions/workflow/status/beidongjiedeguang/openai-forward/run_tests.yml?label=tests">
    </a>
    <a href="https://pypi.org/project/openai_forward/">
        <img alt="pypi downloads" src="https://img.shields.io/pypi/dm/openai_forward">
    </a>
    <a href="https://codecov.io/gh/beidongjiedeguang/openai-forward">
        <img alt="codecov" src="https://codecov.io/gh/beidongjiedeguang/openai-forward/branch/dev/graph/badge.svg">
    </a>
</p>



本项目用于解决一些地区无法直接访问OpenAI的问题，将该服务部署在可以正常访问openai
api的服务器上，通过该服务转发OpenAI的请求。即搭建反向代理服务  
测试访问：https://caloi.top/openai/v1/chat/completions 将等价于 https://api.openai.com/v1/chat/completions  
或者说 https://caloi.top/openai 等价于 https://api.openai.com

# Table of Contents

- [Features](#Features)
- [应用](#应用)
- [安装部署](#安装部署)
- [服务调用](#服务调用)
- [配置选项](#配置选项)
- [聊天日志](#聊天日志)
- [高级配置](#高级配置)

# Features

- [x] 支持转发OpenAI所有接口
- [x] 支持流式响应
- [x] 实时记录聊天记录(包括流式响应的聊天内容)
- [x] 支持默认openai api key(多api key 循环调用)
- [x] 转发api key (在已设置默认openai api key情况下使用)
- [x] docker部署
- [x] 支持指定转发路由前缀
- [x] 支持请求IP验证

# 应用

> 这里以个人使用该项目搭建好的代理服务 https://caloi.top/openai 为例

### [caloi.top](https://caloi.top)

基于开源项目[ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)搭建自己的chatgpt服务  
替换docker启动命令中的 `BASE_URL`为我们自己搭建的代理服务地址

```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="sk-******" \
    -e BASE_URL="caloi.top/openai" \
    -e CODE="<your password>" \
    yidadaa/chatgpt-next-web 
``` 

访问 https://caloi.top 。访问密码为 `beidongjiedeguang`

### 在模块中使用

**JS/TS**

```diff
  import { Configuration } from "openai";
  
  const configuration = new Configuration({
+ basePath: "https://caloi.top/openai/v1",
  apiKey: "sk-******",
  });
```

**Python**

```diff
  import openai
+ openai.api_base = "https://caloi.top/openai/v1"
  openai.api_key = "sk-******"
```

### Image Generation (DALL-E):

```bash
curl --location 'https://caloi.top/openai/v1/images/generations' \
--header 'Authorization: Bearer sk-******' \
--header 'Content-Type: application/json' \
--data '{
    "prompt": "A photo of a cat",
    "n": 1,
    "size": "512x512"
}'
```

# 安装部署

提供3种服务部署方式,选择一种即可

## pip
pip的安装方式目前在使用nginx反向代理时存在Bug, 建议使用Docker方式部署。  
**安装**

```bash
pip install openai-forward
```

**运行转发服务**  
可通过`--port`指定端口号，默认为`8000`，可通过`--workers`指定工作进程数，默认为`1`

```bash
openai_forward run --port=9999 --workers=1
```

服务就搭建完成了，使用方式只需将`https://api.openai.com` 替换为服务所在端口`http://{ip}:{port}` 即可。

当然也可以将 OPENAI_API_KEY 作为环境变量传入作为默认api key， 这样客户端在请求相关路由时可以无需在Header中传入Authorization。
带默认api key的启动方式：

```bash
OPENAI_API_KEY="sk-xxx" openai_forward run --port=9999 --workers=1
```

注: 如果既存在默认api key又在请求头中传入了api key，则以请求头中的api key会覆盖默认api key.

## Docker (推荐)

```bash
docker run --name="openai-forward" -d -p 9999:8000 beidongjiedeguang/openai-forward:latest 
```

将映射宿主机的9999端口，通过`http://{ip}:9999`访问服务。  
注：同样可以在启动命令中通过-e传入环境变量OPENAI_API_KEY=sk-xxx作为默认api key

## 源码部署

```bash
git clone https://github.com/beidongjiedeguang/openai-forward.git --depth=1
cd openai-forward
```

**使用 docker**

```bash
docker-compose up
```

**或使用pip**

```bash
pip install -e .
openai-forward run 
```

# 服务调用

替换openai的api地址为该服务的地址即可，如：

```bash
https://api.openai.com/v1/chat/completions
```

替换为

```bash
http://{ip}:{port}/v1/chat/completions
```

# 配置选项

**`openai-forward run`参数配置项**

| 配置项       | 说明 | 默认值 |
|-----------| --- | :---: |
| --port    | 服务端口号 | 8000 |
| --workers | 工作进程数 | 1 |

**环境变量配置项**  
参考项目根目录下`.env`文件

| 环境变量            | 说明                                                              |           默认值            |
|-----------------|-----------------------------------------------------------------|:------------------------:|
| OPENAI_API_KEY  | 默认openai api key，支持多个默认api key, 以 `sk-` 开头， 以空格分割      |            无             |
| FORWARD_KEY     | 允许调用方使用该key代替openai api key，支持多个forward key, 以`fk-` 开头, 以空格分割 |      无             |
| OPENAI_BASE_URL | 转发base url                                                      | `https://api.openai.com` |
| LOG_CHAT        | 是否记录聊天内容                                                        |          `true`          |
| ROUTE_PREFIX    | 路由前缀                                                            |            无             |
| IP_WHITELIST    | ip白名单, 空格分开                                                     |           无            |
| IP_BLACKLIST    | ip黑名单, 空格分开                                                     |           无            | 

# 聊天日志

保存路径在当前目录下的`Log/`路径中。  
聊天日志以 `chat_`开头, 默认每5轮对话写入一次文件    
记录格式为

```text
{'host': xxx, 'model': xxx, 'message': [{'user': xxx}, {'assistant': xxx}]}
{'assistant': xxx}

{'host': ...}
{'assistant': ...}

...
```

# 高级配置

**设置api_key为自己设置的forward key**  
需要配置 OPENAI_API_KEY 和 FORWARD_KEY, 例如

```bash
OPENAI_API_KEY=sk-*******
FORWARD_KEY=fk-****** # 这里fk-token由我们自己定义
```
这里我们配置了FORWARD_KEY为`fk-******`, 那么后面客户端在调用时只需设置OPENAI_API_KEY为我们自定义的`fk-******` 即可。  
这样的好处是在使用一些需要输入OPENAI_API_KEY的第三方应用时，我们可以使用`fk-******`搭配proxy使用（如下面的例子） 而无需担心OPENAI_API_KEY被泄露。

**用例:**
```bash
curl https://caloi.top/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fk-******" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```
**Python**
```diff
  import openai
+ openai.api_base = "https://caloi.top/openai/v1"
- openai.api_key = "sk-******"
+ openai.api_key = "fk-******"
```
**Web application**
```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="fk-******" \
    -e BASE_URL="caloi.top/openai" \
    -e CODE="<your password>" \
    yidadaa/chatgpt-next-web 
``` 