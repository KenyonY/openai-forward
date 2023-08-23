**中文** | ~~[**English**](./README_EN.md)~~

<h1 align="center">
    <br>
    OpenAI Forward
    <br>
</h1>
<p align="center">
    <b> OpenAI API风格接口转发服务 <br/>
    The fastest way to deploy llms api forwarding </b>
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

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/beidongjiedeguang/openai-forward)

[特点](#特点) |
[部署指南](deploy.md) |
[使用](#使用) |
[配置](#配置) |
[对话日志](#对话日志)


</div>

OpenAI-Forward是大模型与用户层之间的一道转发服务，
用于对请求模型的速率限制，模型返回的Token速率限制，自定义API KEY 等。



<a>
   <img src="https://raw.githubusercontent.com/beidongjiedeguang/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## 特点

OpenAI-Forward支持以下功能:

- **万能代理**: 几乎可以转发任何请求
- **用户速率限制**: 提供请求速率限制(**RPM**)与流式返回的Token速率限制(**TPM**)
- **自定义秘钥**: 支持用户使用自定义生成的秘钥代替原始api key使用。
- 流式响应的对话日志
- 可同时转发多个目标服务至不同路由
- 失败请求自动重试
- 一分钟内完成安装与部署; 一键部署至云端
- ...

由本项目搭建的代理服务地址：
> https://api.openai-forward.com  
> https://render.openai-forward.com

<font size=2 >
注：这里提供的代理服务仅供学习使用。
</font>


## 部署指南

 👉 [部署文档](deploy.md)


<a>
   <img src="https://raw.githubusercontent.com/beidongjiedeguang/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## 使用
**安装**
```bash
pip install openai-forward
```
**运行**
```bash
aifd run
```
如果读入了根路径的`.env`的配置, 将会看到以下启动信息

```bash
❯ aifd run
╭────── 🤗 openai-forward is ready to serve!  ───────╮
│                                                    │
│  base url         https://api.openai.com           │
│  route prefix     /                                │
│  api keys         False                            │
│  forward keys     False                            │
╰────────────────────────────────────────────────────╯
╭──────────── ⏱️ Rate Limit configuration ───────────╮
│                                                    │
│  strategy               moving-window              │
│  /healthz               100/2minutes (req)         │
│  /v1/chat/completions   60/minute;600/hour (req)   │
│  /v1/chat/completions   40/second (token)          │
╰────────────────────────────────────────────────────╯
INFO:     Started server process [33811]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 代理OpenAI API:
这也是`aifd run`的默认选项

#### 在第三方应用中使用

<details >
   <summary> 点击展开</summary>  

基于开源项目[ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)搭建自己的chatgpt服务  
替换docker启动命令中的 `BASE_URL`为自己搭建的代理服务地址

```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="sk-******" \
    -e BASE_URL="https://api.openai-forward.com" \
    -e CODE="******" \
    yidadaa/chatgpt-next-web 
``` 

</details>

#### 在代码中使用

<details >
  <summary>点击展开</summary>

**Python**

```diff
  import openai
+ openai.api_base = "https://api.openai-forward.com/v1"
  openai.api_key = "sk-******"
```

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

### 代理本地模型

与 [LocalAI](https://github.com/go-skynet/LocalAI)，
[api-for-open-llm](https://github.com/xusenlinzy/api-for-open-llm)等
一起使用，赋予这些服务接口的用户请求速率限制，token输出速率限制，对话日志输出等能力。  

以LocalAI为例：  
假设部署的LocalAI服务运行在 `http://localhost:8080`，
那么接下来只需修改环境变量(或[.env](.env)文件)中`OPENAI_BASE_URL=http://localhost:8080` 就可以完成对LocalAI的代理，
然后即可在`aifd`的默认服务端口`http://localhost:8000`中访问LocalAI.

(待补充)

### 代理其它云端模型

例如可通过 [claude-to-chatgpt](https://github.com/jtsang4/claude-to-chatgpt)
将claude的api格式对齐为openai的格式，然后使用`openai-forward`进行代理。
(待补充)

<a>
   <img src="https://raw.githubusercontent.com/beidongjiedeguang/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>


## 配置

### 命令行参数

可通过 `aifd run --help` 查看

<details open>
  <summary>Click for more details</summary>

**`aifd run`参数配置项**

| 配置项        | 说明         |   默认值   |
|------------|------------|:-------:|
| --port     | 服务端口号      |  8000   |
| --workers  | 工作进程数      |    1    |
| --log_chat | 同 LOG_CHAT | `False` |

</details>

### 环境变量配置项

支持从运行目录下的`.env`文件中读取  
配置示例见根目录下的 [.env.example](.env.example)

| 环境变量                | 说明                                                                                                                                |          默认值           |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------|:----------------------:|
| OPENAI_BASE_URL     | 默认 openai官方 api 地址                                                                                                                | https://api.openai.com |
| OPENAI_ROUTE_PREFIX | openai(接口格式)路由前缀                                                                                                                  |           /            |
| OPENAI_API_KEY      | 默认openai api key，支持多个默认api key, 以 `sk-` 开头， 以逗号分隔                                                                                 |           无            |
| FORWARD_KEY         | 允许调用方使用该key代替openai api key，支持多个forward key, 以逗号分隔; 如果设置了OPENAI_API_KEY，而没有设置FORWARD_KEY, 则客户端调用时无需提供密钥, 此时出于安全考虑不建议FORWARD_KEY置空 |           无            |
| EXTRA_BASE_URL      | 额外转发服务地址                                                                                                                          |           无            |
| EXTRA_ROUTE_PREFIX  | 额外转发服务路由前缀                                                                                                                        |           无            |
| REQ_RATE_LIMIT      | 指定路由的请求速率限制（区分用户）                                                                                                                 |           无            |
| GLOBAL_RATE_LIMIT   | 所有`REQ_RATE_LIMIT`没有指定的路由. 不填默认无限制                                                                                                |           无            |
| RATE_LIMIT_STRATEGY | 速率限制策略(fixed-window, fixed-window-elastic-expiry, moving-window)                                                                  |           无            |
| TOKEN_RATE_LIMIT    | 对每一份流式返回的token速率限制 (这里的token并不严格等于gpt中定义的token，而是SSE的chunk)                                                                       |           无            |
| PROXY               | http代理                                                                                                                            |           无            |
| LOG_CHAT            | 是否记录聊天内容                                                                                                                          |        `false`         |

更多见 [.env.example](.env.example) 中的说明。(待完善)

### 自定义秘钥

<details open>
  <summary>Click for more details</summary>

需要配置 OPENAI_API_KEY 和 FORWARD_KEY, 如

```bash
OPENAI_API_KEY=sk-*******
FORWARD_KEY=fk-****** # 这里fk-token由我们自己定义
```

**用例:**

```diff
  import openai
+ openai.api_base = "https://api.openai-forward.com/v1"
- openai.api_key = "sk-******"
+ openai.api_key = "fk-******"
```

</details>

### 多目标服务转发

支持转发不同地址的服务至同一端口的不同路由下
用例见  `.env.example`

### 对话日志

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
