**中文** | [**English**](./README.md)

<h1 align="center">
    <br>
    OpenAI Forward
    <br>
</h1>
<p align="center">
    <b> OpenAI API 接口转发服务 <br/>
    The fastest way to deploy openai api forwarding </b>
</p>

[//]: # (    <a href="https://github.com/beidongjiedeguang">)

[//]: # (        <img alt="name" src="https://img.shields.io/badge/author-@kunyuan-orange.svg?style=flat-square&logo=appveyor">)

[//]: # (    </a>)

[//]: # (    <a href="https://github.com/beidongjiedeguang/openai-forward/stargazers">)

[//]: # (        <img alt="starts" src=https://img.shields.io/github/stars/beidongjiedeguang/openai-forward?style=social>)

[//]: # (    </a>)

[//]: # ([![Downloads]&#40;https://static.pepy.tech/badge/openai-forward/month&#41;]&#40;https://pepy.tech/project/openai-forward&#41;)

[//]: # (    <a href="https://codecov.io/gh/beidongjiedeguang/openai-forward">)

[//]: # (        <img alt="codecov" src="https://codecov.io/gh/beidongjiedeguang/openai-forward/branch/dev/graph/badge.svg">)

[//]: # (    </a>)

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

</p>



本项目用于解决一些地区无法直接访问OpenAI的问题，将该服务部署在可以正常访问openai
api的服务器上，通过该服务转发OpenAI的请求。即搭建反向代理服务  
测试访问：https://caloi.top/openai/v1/chat/completions 将等价于 https://api.openai.com/v1/chat/completions  
或者说 https://caloi.top/openai 等价于 https://api.openai.com 

# Table of Contents

- [Features](#Features)
- [Usage](#Usage)
- [安装部署](#安装部署)
- [服务调用](#服务调用)
- [配置选项](#配置选项)

# Features

- [x] 支持转发OpenAI所有接口
- [x] 支持流式响应
- [x] 支持默认api key(多api key 循环调用)
- [x] pip安装部署
- [x] docker部署
- [x] 支持多进程转发
- [x] 支持指定转发路由前缀
- [x] 支持请求IP验证

# Usage

> 这里以个人使用该项目搭建好的代理服务 https://caloi.top/openai 为例

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

### [chatgpt-web](https://github.com/Chanzhaoyu/chatgpt-web)

修改 [Docker Compose](https://github.com/Chanzhaoyu/chatgpt-web#docker-compose) 中的`OPENAI_API_BASE_URL`
为我们搭建的代理服务地址:

```bash
OPENAI_API_BASE_URL: https://caloi.top/openai 
```

### [ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)

替换docker启动命令中的 `BASE_URL`为我们搭建的代理服务地址

```bash
docker run -d -p 3000:3000 -e OPENAI_API_KEY="sk-xxx" -e CODE="<your password>" -e BASE_URL="caloi.top/openai" yidadaa/chatgpt-next-web
```

# 安装部署

提供两种服务部署方式,选择一种即可

## pip (推荐)

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

## Docker

```bash
docker run --name="openai-forward" -d -p 9999:8000 beidongjiedeguang/openai-forward:latest 
```

将映射宿主机的9999端口，通过`http://{ip}:9999`访问服务。  
注：同样可以在启动命令中通过-e传入环境变量OPENAI_API_KEY=sk-xxx作为默认api key

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

| 环境变量      | 说明                             |           默认值            |
|-----------------|--------------------------------|:------------------------:|
| OPENAI_API_KEY  | 默认api key，支持多个默认api key, 以空格分割 |            无             |
| OPENAI_BASE_URL | 转发base url                     | `https://api.openai.com` |
|LOG_CHAT| 是否记录聊天内容                       |          `true`          |
|ROUTE_PREFIX| 路由前缀                           |            无             |
| IP_WHITELIST    | ip白名单, 空格分开                    |           无            |
| IP_BLACKLIST    | ip黑名单, 空格分开                    |           无            | 

