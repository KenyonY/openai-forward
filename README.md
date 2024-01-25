**简体中文** | [**English**](https://github.com/KenyonY/openai-forward/blob/main/README_EN.md)

<h1 align="center">
    <a href="https://github.com/KenyonY/openai-forward"> 🌠 OpenAI Forward </a>
    <br>
    <br>
</h1>

<p align="center">
    <a href="https://pypi.org/project/openai-forward/">
        <img src="https://img.shields.io/pypi/v/openai-forward?color=brightgreen&style=flat-square" alt="PyPI version" >
    </a>
    <a href="https://github.com/KenyonY/openai-forward/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/github/license/KenyonY/openai-forward.svg?color=blue&style=flat-square">
    </a>
    <a href="https://hub.docker.com/r/beidongjiedeguang/openai-forward">
        <img alt="docker pull" src="https://img.shields.io/docker/pulls/beidongjiedeguang/openai-forward?style=flat-square&label=docker pulls">
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

**OpenAI-Forward** 是为大型语言模型实现的高效转发服务。其核心功能包括
用户请求速率控制、Token速率限制、智能预测缓存、日志管理和API密钥管理等，旨在提供高效、便捷的模型转发服务。
无论是代理本地语言模型还是云端语言模型，如 [LocalAI](https://github.com/go-skynet/LocalAI) 或 [OpenAI](https://api.openai.com)，都可以由 OpenAI Forward 轻松实现。
得益于 [uvicorn](https://github.com/encode/uvicorn), [aiohttp](https://github.com/aio-libs/aiohttp), 和 [asyncio](https://docs.python.org/3/library/asyncio.html)
等库支持，OpenAI-Forward 实现了出色的异步性能。

### News
- 🚀🚀 从v0.7.0版本后支持通过WebUI进行配置管理
- gpt-1106版本已适配
- 缓存后端切换为高性能数据库后端：[🗲 FlaxKV](https://github.com/KenyonY/flaxkv)


<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## 主要特性

OpenAI-Forward 提供以下核心功能：

- **全能转发**：可转发几乎所有类型的请求
- **性能优先**：出色的异步性能
- **缓存AI预测**：对AI预测进行缓存，加速服务访问并节省费用
- **用户流量控制**：自定义请求速率与Token速率
- **实时响应日志**：提升LLMs可观察性
- **自定义秘钥**：替代原始API密钥
- **多目标路由**：转发多个服务地址至同一服务下的不同路由
- **自动重试**：确保服务的稳定性，请求失败时将自动重试
- **快速部署**：支持通过pip和docker在本地或云端进行快速部署



**由本项目搭建的代理服务地址:**

- 原始OpenAI 服务地址
  > https://api.openai-forward.com  
  > https://render.openai-forward.com

- 开启缓存的服务地址（用户请求结果将被保存一段时间）
  > https://smart.openai-forward.com

<sub>
注：此处部署的代理服务仅供个人学习和研究目的使用，勿用于任何商业用途。
</sub>

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
# 或安装webui版本：
pip install openai-forward[webui]
```

**启动服务**

```bash
aifd run
# 或启动带webui的服务
aifd run --webui
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

**Python**

```diff
  from openai import OpenAI  # pip install openai>=1.0.0
  client = OpenAI(
+     base_url="https://api.openai-forward.com/v1", 
      api_key="sk-******"
  )
```

<details >
   <summary> 更多</summary>  

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

- **场景1:**
  使用通用转发,由环境变量中`EXTRA_BASE_URL`与`EXTRA_ROUTE_PREFIX` 两变量控制，可对任意来源服务进行转发，
  可获得请求速率控制与token速率控制；但通用转发不支持自定义秘钥、实时日志和缓存AI响应.

- **场景2：**
  可通过 [LiteLLM](https://github.com/BerriAI/litellm) 可以将 众多云模型的 API 格式转换为 openai
  的api格式，然后使用openai风格转发(即`OPENAI_BASE_URL`) 


(更多)

### 代理ChatGPT
[参考](./deploy.md)


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
| CACHE_BACKEND         | cache后端，支持内存后端和数据库后端，默认为内存后端，可选lmdb、leveldb数据库后端                     |         `lmdb`         |
| CACHE_CHAT_COMPLETION | 是否缓存/v1/chat/completions 结果                                          |        `false`         |
| DEFAULT_REQUEST_CACHING_VALUE | 是否默认开启缓存                                                           |        `false`         |

详细配置说明可参见 [.env.example](.env.example) 文件。(待完善)

> 注意：如果你设置了 OPENAI_API_KEY 但未设置 FORWARD_KEY，客户端在调用时将不需要提供密钥。由于这可能存在安全风险，除非有明确需求，否则不推荐将
> FORWARD_KEY 置空。

### 智能缓存

缓存可选择数据库后端，需安装相应的环境：

- 配置环境变量中`CACHE_BACKEND`以使用相应的数据库后端进行存储。 可选值`LMDB`、`LEVELDB`
- 配置`CACHE_CHAT_COMPLETION`为`true`以缓存/v1/chat/completions 结果。

**Python**
```diff
  from openai import OpenAI 
  client = OpenAI(
+     base_url="https://smart.openai-forward.com/v1", 
      api_key="sk-******"
  )
  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "user", "content": "Hello!"}
    ],
+   extra_body={"caching": True}
)
```
**Curl**  
```bash
curl https://smart.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-******" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "caching": true
  }'

```

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
{'assistant': 'Hello! How can I assist you today?', 'is_tool_calls': False, 'uid': '2155fe1580e6aed626aa1ad74c1ce54e'}
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
    "tools": null,
    "is_tool_calls": false,
    "assistant": "Hello! How can I assist you today?"
  }
]
```

</details>

## 贡献
欢迎通过提交拉取请求或在仓库中提出问题来为此项目做出贡献。

## 赞助者与支持者

<a href="https://www.jetbrains.com/?from=KenyonY/openai-forward" target="_blank">
<img src="https://raw.githubusercontent.com/KenyonY/openai-forward/e7da8de4a48611b84430ca3ea44d355578134b85/.github/images/jetbrains.svg" width="100px" height="100px">
</a>

## 许可证

OpenAI-Forward 采用 [MIT](https://opensource.org/license/mit/) 许可证。
