**中文** | ~~[**English**](./README_EN.md)~~

<h1 align="center">
    <br>
    OpenAI Forward
    <br>
</h1>
<p align="center">
    <b> OpenAI API风格接口转发服务 <br/>
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
        <img alt="docker image size" src="https://img.shields.io/docker/image-size/beidongjiedeguang/openai-forward?style=flat&label=docker image">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward/actions/workflows/ci.yml">
        <img alt="tests" src="https://img.shields.io/github/actions/workflow/status/beidongjiedeguang/openai-forward/ci.yml?label=tests">
    </a>
    <a href="https://pypistats.org/packages/openai-forward">
        <img alt="pypi downloads" src="https://img.shields.io/pypi/dm/openai_forward">
    </a>
    <a href="https://codecov.io/gh/beidongjiedeguang/openai-forward">
        <img alt="codecov" src="https://codecov.io/gh/beidongjiedeguang/openai-forward/branch/dev/graph/badge.svg">
    </a>
</p>

<div align="center">

[功能](#功能) |
[部署指南](#部署指南) |
[应用](#应用) |
[配置选项](#配置选项) |
[对话日志](#对话日志)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/tejCum?referralCode=U0-kXv)  
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/beidongjiedeguang/openai-forward)

</div>

本项目是大模型与用户层之间的一道转发服务，可用于搭建反向代理，自定义API KEY，请求速率限制，token速率限制等.


<a>
   <img src="https://raw.githubusercontent.com/beidongjiedeguang/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

由本项目搭建的长期代理地址：
> https://api.openai-forward.com  
> https://render.openai-forward.com  
> https://cloudflare.page.openai-forward.com  
> https://vercel.openai-forward.com  


### 特色
-  万能转发: 支持转发OpenAI所有接口以及SSE流式响应
-  支持指定转发路由前缀
-  自定义转发api key 
-  流式响应对话日志
-  多接口转发
-  请求速率限制(RPM)
-  流式返回的token速率限制(TPM)

## 部署指南

👉 [部署文档](deploy.md)

提供以下几种部署方式  
**有海外vps方案**

1. [pip 安装部署](deploy.md#pip部署)
2. [Docker部署](deploy.md#docker部署)

**无vps免费部署方案**

1. [Railway部署](deploy.md#Railway-一键部署)
2. [Render一键部署](deploy.md#render-一键部署)

---
下面的部署仅提供单一转发功能

3. [一键Vercel部署](deploy.md#vercel-一键部署)
4. [cloudflare部署](deploy.md#cloudflare-部署)

## 应用

### [聊天应用](https://chat.beidongjiedeguang.top)

基于开源项目[ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)搭建自己的chatgpt服务  
替换docker启动命令中的 `BASE_URL`为我们自己搭建的代理服务地址


<details open>
   <summary> details</summary>  

```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="sk-******" \
    -e BASE_URL="https://api.openai-forward.com" \
    -e CODE="******" \
    yidadaa/chatgpt-next-web 
``` 

</details>

### 在代码中使用

**Python**

```diff
  import openai
+ openai.api_base = "https://api.openai-forward.com/v1"
  openai.api_key = "sk-******"
```

<details open>
  <summary>More Examples</summary>

**JS/TS**

```diff
  import { Configuration } from "openai";
  
  const configuration = new Configuration({
+ basePath: "https://api.openai-forward.com/v1",
  apiKey: "sk-******",
  });
```

**gpt-3.5-turbo**

```bash
curl https://api.openai-forward.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-******" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**Image Generation (DALL-E)**

```bash
curl --location 'https://api.openai-forward.com/v1/images/generations' \
--header 'Authorization: Bearer sk-******' \
--header 'Content-Type: application/json' \
--data '{
    "prompt": "A photo of a cat",
    "n": 1,
    "size": "512x512"
}'
```

</details>

## 配置

配置的设置方式支持两种  
一种为在命令行中执行`aifd run` 的运行参数(如`--port=8000`)中指定;  
另一种为读取环境变量的方式指定。

### 命令行参数

可通过 `aifd run --help` 查看

<details open>
  <summary>Click for more details</summary>

**`aifd run`参数配置项**

| 配置项                   | 说明                    |          默认值           |
|-----------------------|-----------------------|:----------------------:|
| --port                | 服务端口号                 |          8000          |
| --workers             | 工作进程数                 |           1            |
| --log_chat            | 同 LOG_CHAT            |        `False`         |

</details>

### 环境变量配置项

支持从运行目录下的`.env`文件中读取  
配置示例见根目录下的`.env.example`  

| 环境变量                | 说明                                                                                                                                |          默认值           |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------|:----------------------:|
| OPENAI_BASE_URL     | 默认 openai官方 api 地址                                                                                                                | https://api.openai.com |
| OPENAI_ROUTE_PREFIX | openai(接口格式)路由前缀                                                                                                                  |           /            |
| OPENAI_API_KEY      | 默认openai api key，支持多个默认api key, 以 `sk-` 开头， 以逗号分隔                                                                                 |           无            |
| FORWARD_KEY         | 允许调用方使用该key代替openai api key，支持多个forward key, 以逗号分隔; 如果设置了OPENAI_API_KEY，而没有设置FORWARD_KEY, 则客户端调用时无需提供密钥, 此时出于安全考虑不建议FORWARD_KEY置空 |           无            |
| EXTRA_BASE_URL      | 额外转发服务地址                                                                                                                          |           无            |
| EXTRA_ROUTE_PREFIX  | 额外转发服务路由前缀                                                                                                                        |           无            |
| LOG_CHAT            | 是否记录聊天内容                                                                                                                          |        `false`         |


### 设置openai api_key为自定义的forward key
<details open>
  <summary>Click for more details</summary>

需要配置 OPENAI_API_KEY 和 FORWARD_KEY, 如

```bash
OPENAI_API_KEY=sk-*******
FORWARD_KEY=fk-****** # 这里fk-token由我们自己定义
```

**用例:**

```bash
curl https://api.openai-forward.com/v1/chat/completions \
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
+ openai.api_base = "https://api.openai-forward.com/v1"
- openai.api_key = "sk-******"
+ openai.api_key = "fk-******"
```

**Web application**

```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="fk-******" \
    -e BASE_URL="https://api.openai-forward.com" \
    -e CODE="<your password>" \
    yidadaa/chatgpt-next-web 
``` 

</details>

### 多路由转发

支持转发不同地址的服务至同一端口的不同路由下，基本可以转发任何服务。  
用例见  `.env.example`


## 对话日志

默认不记录对话日志，若要开启需设置环境变量`LOG_CHAT=true`
<details open>
  <summary>Click for more details</summary>

保存路径在当前目录下的`Log/chat`路径中。  
记录格式为

```text
{'messages': [{'user': 'hi'}], 'model': 'gpt-3.5-turbo', 'forwarded-for': '', 'uid': '467a17ec-bf39-4b65-9ebd-e722b3bdd5c3', 'datetime': '2023-07-18 14:01:21'}
{'assistant': 'Hello there! How can I assist you today?', 'uid': '467a17ec-bf39-4b65-9ebd-e722b3bdd5c3'}
{'messages': [{'user': 'Hello!'}], 'model': 'gpt-3.5-turbo', 'forwarded-for': '', 'uid': 'f844d156-e747-4887-aef8-e40d977b5ee7', 'datetime': '2023-07-18 14:01:23'}
{'assistant': 'Hi there! How can I assist you today?', 'uid': 'f844d156-e747-4887-aef8-e40d977b5ee7'}
```

转换为`json`格式：

```bash
aifd convert
```

得到`chat.json`：

```json
[
    {
        "datetime": "2023-07-18 14:01:21",
        "forwarded-for": "",
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "user": "hi"
            }
        ],
        "assistant": "Hello there! How can I assist you today?"
    },
    {
        "datetime": "2023-07-18 14:01:23",
        "forwarded-for": "",
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "user": "Hello!"
            }
        ],
        "assistant": "Hi there! How can I assist you today?"
    }
]
```

</details>

## Backer and Sponsor

<a href="https://www.jetbrains.com/?from=beidongjiedeguang/openai-forward" target="_blank">
<img src=".github/images/jetbrains.svg" width="100px" height="100px">
</a>

## License

OpenAI-Forward is licensed under the [MIT](https://opensource.org/license/mit/) license.
