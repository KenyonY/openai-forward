**中文** | ~~[**English**](./README_EN.md)~~

<h1 align="center">
    <br>
    OpenAI Forward
    <br>
</h1>

<div align=center><img src=https://github.com/KenyonY/openai-forward/blob/main/.github/data/logo.png?raw=true width="240px"></div>


<p align="center">
    <a href="https://pypi.org/project/openai-forward/">
        <img src="https://img.shields.io/pypi/v/openai-forward?color=brightgreen&style=flat-square" alt="PyPI version" >
    </a>
    <a href="https://github.com/KenyonY/openai-forward/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/github/license/KenyonY/openai-forward.svg?color=blue&style=flat-square">
    </a>
    <a href="https://github.com/KenyonY/openai-forward/releases">
        <img alt="Release (latest by date)" src="https://img.shields.io/github/v/release/KenyonY/openai-forward?&style=flat-square">
    </a>
    <a href="https://hub.docker.com/r/beidongjiedeguang/openai-forward">
        <img alt="docker image size" src="https://img.shields.io/docker/image-size/beidongjiedeguang/openai-forward?style=flat-square&label=docker image">
    </a>
    <a href="https://github.com/KenyonY/openai-forward/actions/workflows/ci.yml">
        <img alt="tests" src="https://img.shields.io/github/actions/workflow/status/KenyonY/openai-forward/ci.yml?style=flat-square&label=tests">
    </a>
    <a href="https://pypistats.org/packages/openai-forward">
        <img alt="pypi downloads" src="https://img.shields.io/pypi/dm/openai_forward?style=flat-square">
    </a>
</p>

<div align="center">

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/KenyonY/openai-forward)

[特点](#主要特性) |
[部署指南](deploy.md) |
[使用指南](#使用指南) |
[配置](#配置) |
[对话日志](#对话日志)


</div>

openai-forward
是一个专为大型语言模型设计的高级转发服务，提供包括用户请求速率控制、Token速率限制、日志记录和自定义API密钥等功能。
该服务可用于代理本地模型（如 [LocalAI](https://github.com/go-skynet/LocalAI)
）或云端模型（如 [OpenAI](https://api.openai.com)）。
服务由 `fastapi`,`aiohttp`,`asyncio`完全异步实现。


<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## 主要特性

OpenAI-Forward 提供如下功能：

- **全能代理**: 具备转发几乎所有类型请求的能力
- **缓存AI预测**: 开启对ai生成结果的缓存，显著加快服务访问时间&&节省金币
- **用户流量控制**: 自定义用户请求速率控制（RPM）和流式Token速率控制（TPM）
- **实时响应日志**: 支持流式响应的会话日志记录，提供了对Prompt调用链良好的可观察性
- **自定义秘钥**: 允许用户用自定义生成的密钥替代原始API密钥
- **多目标路由**: 能够同时转发多个服务到不同的路由地址
- **自动重试机制**：在请求失败时自动重试
- **快速部署**: `pip`/`docker` 快速本地安装和部署，支持一键云端部署

**由本项目搭建的代理服务**

与OpenAI完全一致 服务地址
> https://api.openai-forward.com  
> https://render.openai-forward.com


开启缓存服务地址（用户请求结果将被保存一段时间）
> https://smart.openai-forward.com

<font size=2 >
注：此代理服务仅供个人学习和研究目的使用，勿用于任何商业用途。
</font>

## 部署指南

👉 [部署文档](deploy.md)


<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## 使用指南

### 快速入门

**安装**

```bash
pip install openai-forward
```

**启动服务**

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
│  cache_backend    MEMORY                           │
╰────────────────────────────────────────────────────╯
╭──────────── ⏱️ Rate Limit configuration ───────────╮
│                                                    │
│  backend                memory                     │
│  strategy               moving-window              │
│  global rate limit      100/minute (req)           │
│  /v1/chat/completions   100/2minutes (req)         │
│  /v1/completions        60/minute;600/hour (req)   │
│  /v1/chat/completions   60/second (token)          │
│  /v1/completions        60/second (token)          │
╰────────────────────────────────────────────────────╯
INFO:     Started server process [191471]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 代理OpenAI模型:

`aifd run`的默认选项便是代理`https://api.openai.com`

下面以搭建好的服务地址`https://api/openai-forward.com` 为例

<details >
   <summary> 点击展开</summary>  

#### 在三方应用中使用

基于开源项目[ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)中接入:   
替换docker启动命令中的 `BASE_URL`为自己搭建的代理服务地址

```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="sk-******" \
    -e BASE_URL="https://api.openai-forward.com" \
    -e CODE="******" \
    yidadaa/chatgpt-next-web 
``` 

#### 在代码中接入

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

- **适用场景：** 与 [LocalAI](https://github.com/go-skynet/LocalAI)，
  [api-for-open-llm](https://github.com/xusenlinzy/api-for-open-llm)等项目一起使用

- **如何操作：**
  以LocalAI为例，如果已在 http://localhost:8080 部署了LocalAI服务，仅需在环境变量或 .env
  文件中设置 `OPENAI_BASE_URL=http://localhost:8080`。
  然后即可通过访问 http://localhost:8000 使用LocalAI。

(更多)

### 代理其它云端模型

- **适用场景：**
  例如，通过 [claude-to-chatgpt](https://github.com/jtsang4/claude-to-chatgpt) 可以将 claude 的 API 格式转换为 openai
  的api格式，
  然后使用本服务进行代理。

(更多)

<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## 配置

### 命令行参数

执行 `aifd run --help` 获取参数详情

<details open>
  <summary>Click for more details</summary>

| 配置项       | 说明    | 默认值  |
|-----------|-------|:----:|
| --port    | 服务端口号 | 8000 |
| --workers | 工作进程数 |  1   |

</details>

### 环境变量详情

你可以在项目的运行目录下创建 .env 文件来定制各项配置。参考配置可见根目录下的
[.env.example](.env.example)文件

| 环境变量                  | 说明                                                                   |          默认值           |
|-----------------------|----------------------------------------------------------------------|:----------------------:|
| OPENAI_BASE_URL       | 设置OpenAI API风格的基础地址                                                  | https://api.openai.com |
| OPENAI_ROUTE_PREFIX   | 为OPENAI_BASE_URL接口地址定义路由前缀                                           |           /            |
| OPENAI_API_KEY        | 配置OpenAI 接口风格的API密钥，支持使用多个密钥，通过逗号分隔                                  |           无            |
| FORWARD_KEY           | 设定用于代理的自定义密钥，多个密钥可用逗号分隔。如果未设置(不建议)，将直接使用 `OPENAI_API_KEY`            |           无            |
| EXTRA_BASE_URL        | 用于配置额外代理服务的基础URL                                                     |           无            |
| EXTRA_ROUTE_PREFIX    | 定义额外代理服务的路由前缀                                                        |           无            |
| REQ_RATE_LIMIT        | 设置特定路由的用户请求速率限制 (区分用户)                                               |           无            |
| GLOBAL_RATE_LIMIT     | 配置全局请求速率限制，适用于未在 `REQ_RATE_LIMIT` 中指定的路由                             |           无            |
| RATE_LIMIT_STRATEGY   | 选择速率限制策略，选项包括：fixed-window、fixed-window-elastic-expiry、moving-window |           无            |
| TOKEN_RATE_LIMIT      | 限制流式响应中每个token（或SSE chunk）的输出速率                                      |           无            |
| PROXY                 | 设置HTTP代理地址                                                           |           无            |
| LOG_CHAT              | 开关聊天内容的日志记录，用于调试和监控                                                  |        `false`         |
| CACHE_BACKEND         | cache后端，支持内存后端和数据库后端，默认为内存后端，可选lmdb, rocksdb和leveldb数据库后端            |        `MEMORY`        |
| CACHE_CHAT_COMPLETION | 是否缓存/v1/chat/completions 结果                                          |        `false`         |

详细配置说明可参见 [.env.example](.env.example) 文件。(待完善)

> 注意：如果你设置了 OPENAI_API_KEY 但未设置 FORWARD_KEY，客户端在调用时将不需要提供密钥。由于这可能存在安全风险，除非有明确需求，否则不推荐将
> FORWARD_KEY 置空。

### Caching

缓存默认使用内存后端，可选择数据库后端，需安装相应的环境：

```bash
pip install openai-forward[lmdb] # lmdb后端
pip install openai-forward[leveldb] # leveldb后端
pip install openai-forward[rocksdb] # rocksdb后端
```

- 配置环境变量中`CACHE_BACKEND`以使用相应的数据库后端进行存储。 可选值`MEMORY`、`LMDB`、`ROCKSDB`、`LEVELDB`
- 配置`CACHE_CHAT_COMPLETION`为`true`以缓存/v1/chat/completions 结果。

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

保存路径在当前目录下的`Log/openai/chat/chat.log`路径中。  
记录格式为

```text
{'messages': [{'role': 'user', 'content': 'hi'}], 'model': 'gpt-3.5-turbo', 'stream': True, 'max_tokens': None, 'n': 1, 'temperature': 1, 'top_p': 1, 'logit_bias': None, 'frequency_penalty': 0, 'presence_penalty': 0, 'stop': None, 'user': None, 'ip': '127.0.0.1', 'uid': '2155fe1580e6aed626aa1ad74c1ce54e', 'datetime': '2023-10-17 15:27:12'}
{'assistant': 'Hello! How can I assist you today?', 'is_function_call': False, 'uid': '2155fe1580e6aed626aa1ad74c1ce54e'}
```

转换为`json`格式：

```bash
aifd convert
```

得到`chat_openai.json`：

```json
[
  {
    "datetime": "2023-10-17 15:27:12",
    "ip": "127.0.0.1",
    "model": "gpt-3.5-turbo",
    "temperature": 1,
    "messages": [
      {
        "user": "hi"
      }
    ],
    "functions": null,
    "is_function_call": false,
    "assistant": "Hello! How can I assist you today?"
  }
]
```

</details>

## Backer and Sponsor

<a href="https://www.jetbrains.com/?from=KenyonY/openai-forward" target="_blank">
<img src="https://raw.githubusercontent.com/KenyonY/openai-forward/e7da8de4a48611b84430ca3ea44d355578134b85/.github/images/jetbrains.svg" width="100px" height="100px">
</a>

## License

OpenAI-Forward is licensed under the [MIT](https://opensource.org/license/mit/) license.
