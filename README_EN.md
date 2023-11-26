**English** | [**简体中文**](https://github.com/KenyonY/openai-forward/blob/main/README.md)

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


[Features](#Key-Features) |
[Deployment Guide](deploy_en.md) |
[User Guide](#User-Guide) |
[Configuration](#Configuration) |
[Conversation Logs](#Conversation-Logs)



</div>

---

**OpenAI-Forward** is an efficient forwarding service designed for large language models. 
Its core features include user request rate control, Token rate limits, intelligent prediction caching, 
log management, and API key management, aiming to provide a fast and convenient model forwarding 
service. Whether proxying local language models or cloud-based language models,
such as [LocalAI](https://github.com/go-skynet/LocalAI) or [OpenAI](https://api.openai.com),
OpenAI Forward facilitates easy implementation. 
With the support of libraries like [uvicorn](https://github.com/encode/uvicorn), [aiohttp](https://github.com/aio-libs/aiohttp), and [asyncio](https://docs.python.org/3/library/asyncio.html), 
OpenAI-Forward achieves impressive asynchronous performance.


### News
- Adapted to GPT-1106 version.
- The cache backend is switched to [🗲 FlaxKV](https://github.com/KenyonY/flaxkv)
 
<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=3px width="100%">
</a>

## Key Features

OpenAI-Forward offers the following capabilities:

- **Universal Forwarding**: Supports forwarding of almost all types of requests.
- **Performance First**: Boasts outstanding asynchronous performance.
- **Cache AI Predictions**: Caches AI predictions, accelerating service access and saving costs.
- **User Traffic Control**: Customize request and Token rates.
- **Real-time Response Logs**: Enhances observability of the call chain.
- **Custom Secret Keys**: Replaces the original API keys.
- **Multi-target Routing**: Forwards to multiple service addresses under a single service to different routes.
- **Automatic Retries**: Ensures service stability; will automatically retry on failed requests.
- **Quick Deployment**: Supports fast deployment locally or on the cloud via pip and docker.

**Proxy services set up by this project include**:

- Original OpenAI Service Address:
  > https://api.openai-forward.com  
  > https://render.openai-forward.com

- Cached Service Address (User request results will be saved for some time):
  > https://smart.openai-forward.com

<sub>
Note: The proxy services deployed here are for personal learning and research purposes only and should not be used for any commercial purposes.
</sub>



---

## Deployment Guide

👉 [Deployment Documentation](deploy_en.md)

<a>
<img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## User Guide

### Quick Start

**Installation**

```bash
pip install openai-forward
```

**Starting the Service**

```bash
aifd run
```

If the configuration from the `.env` file at the root path is read, you will see the following startup information.

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

---

### Proxy OpenAI Model:

The default option for `aifd run` is to proxy `https://api.openai.com`.

The following uses the set up service address `https://api.openai-forward.com` as an example.

**Python**

```diff
  from openai import OpenAI  # pip install openai>=1.0.0
  client = OpenAI(
+     base_url="https://api.openai-forward.com/v1", 
      api_key="sk-******"
  )
```

<details>
   <summary> More </summary>

#### Use in Third-party Applications

Integrate within the open-source project [ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web):
Replace the `BASE_URL` in the Docker startup command with the address of your self-hosted proxy service.

```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="sk-******" \
    -e BASE_URL="https://api.openai-forward.com" \
    -e CODE="******" \
    yidadaa/chatgpt-next-web 
``` 

#### Integrate within Code

---


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

---
### Proxy Local Model

- **Applicable scenarios:** To be used in conjunction with projects such as [LocalAI](https://github.com/go-skynet/LocalAI) and [api-for-open-llm](https://github.com/xusenlinzy/api-for-open-llm).

- **How to operate:** 
  Using LocalAI as an example, if the LocalAI service has been deployed at http://localhost:8080, you only need to set `OPENAI_BASE_URL=http://localhost:8080` in the environment variable or in the .env file.
  After that, you can access LocalAI through http://localhost:8000.

(More)

### Proxy Other Cloud Models

- **Applicable scenarios:** 
  For instance, through [LiteLLM](https://github.com/BerriAI/litellm), you can convert the API format of many cloud models to the OpenAI API format and then use this service as a proxy.

(More)

<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## Configuration

### Command Line Arguments

Execute `aifd run --help` to get details on arguments.

<details open>
  <summary>Click for more details</summary>

| Configuration | Description | Default Value |
|---------------|-------------|:-------------:|
| --port       | Service port | 8000         |
| --workers    | Number of working processes | 1 |

</details>

### Environment Variable Details

You can create a .env file in the project's run directory to customize configurations. For a reference configuration, see the [.env.example](.env.example) file in the root directory.

| Environment Variable  | Description                                                                                      | Default Value                 |
|-----------------------|-------------------------------------------------------------------------------------------------|:-----------------------------:|
| OPENAI_BASE_URL       | Set base address for OpenAI-style API                                                            | https://api.openai.com        |
| OPENAI_ROUTE_PREFIX   | Define a route prefix for the OPENAI_BASE_URL interface address                                 | /                             |
| OPENAI_API_KEY        | Configure API key in OpenAI style, supports using multiple keys separated by commas              | None                          |
| FORWARD_KEY           | Set a custom key for proxying, multiple keys can be separated by commas. If not set (not recommended), it will directly use `OPENAI_API_KEY` | None |
| EXTRA_BASE_URL        | Configure the base URL for additional proxy services                                             | None                          |
| EXTRA_ROUTE_PREFIX    | Define the route prefix for additional proxy services                                           | None                          |
| REQ_RATE_LIMIT        | Set the user request rate limit for specific routes (user distinguished)                         | None                          |
| GLOBAL_RATE_LIMIT     | Configure a global request rate limit applicable to routes not specified in `REQ_RATE_LIMIT`    | None                          |
| RATE_LIMIT_STRATEGY   | Choose a rate limit strategy, options include: fixed-window, fixed-window-elastic-expiry, moving-window | None |
| TOKEN_RATE_LIMIT      | Limit the output rate of each token (or SSE chunk) in a streaming response                      | None                          |
| PROXY                 | Set HTTP proxy address                                                                           | None                          |
| LOG_CHAT              | Toggle chat content logging for debugging and monitoring                                        | `false`                       |
| CACHE_BACKEND         | Cache backend, supports memory backend and database backend. By default, it's memory backend, optional database backends are lmdb, rocksdb, and leveldb | `MEMORY` |
| CACHE_CHAT_COMPLETION | Whether to cache /v1/chat/completions results                                                    | `false`                       |

Detailed configuration descriptions can be seen in the [.env.example](.env.example) file. (To be completed)

> Note: If you set OPENAI_API_KEY but did not set FORWARD_KEY, clients will not need to provide a key when calling. As this may pose a security risk, it's not recommended to leave FORWARD_KEY unset unless there's a specific need.

### Caching


- Configure `CACHE_BACKEND` in the environment variable to use the respective database backend for storage. Options are `MEMORY`, `LMDB`, and `LEVELDB`.
- Set `CACHE_CHAT_COMPLETION` to `true` to cache /v1/chat/completions results.

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

### Custom Keys

<details open>
  <summary>Click for more details</summary>

Configure OPENAI_API_KEY and FORWARD_KEY, for example:

```bash
OPENAI_API_KEY=sk-*******
FORWARD_KEY=fk-****** # Here, the fk-token is customized
```

**Use case:**

```diff
  import openai
+ openai.api_base = "https://api.openai-forward.com/v1"
- openai.api_key = "sk-******"
+ openai.api_key = "fk-******"
```

</details>

### Multi-Target Service Forwarding

Supports forwarding services from different addresses to different routes under the same port. Refer to the `.env.example` for examples.

### Conversation Logs

Chat logs are not recorded by default. If you wish to enable it, set the `LOG_CHAT=true` environment variable.
<details open>
  <summary>Click for more details</summary>

Logs are saved in the current directory under `Log/openai/chat/chat.log`. The recording format is:
```text
{'messages': [{'role': 'user', 'content': 'hi'}], 'model': 'gpt-3.5-turbo', 'stream': True, 'max_tokens': None, 'n': 1, 'temperature': 1, 'top_p': 1, 'logit_bias': None, 'frequency_penalty': 0, 'presence_penalty': 0, 'stop': None, 'user': None, 'ip': '127.0.0.1', 'uid': '2155fe1580e6aed626aa1ad74c1ce54e', 'datetime': '2023-10-17 15:27:12'}
{'assistant': 'Hello! How can I assist you today?', 'is_function_call': False, 'uid': '2155fe1580e6aed626aa1ad74c1ce54e'}
```


To convert to `json` format:

```bash
aifd convert
```

You'll get `chat_openai.json`:
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
