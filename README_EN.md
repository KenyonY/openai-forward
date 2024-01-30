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

> [!IMPORTANT]
>
> Significant configuration adjustments will be made after version v0.7.0, making it incompatible with previous versions.
> Configuring through the UI will be more convenient, and more powerful configuration options are provided.



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
- **Black and White List**: IP-based black and white list restrictions can be implemented.
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

# Or install `webui` version(Currently in alpha version)：
git clone https://github.com/KenyonY/openai-forward.git
cd openai-forward
pip install -e .[webui]
```

**Starting the Service**

```bash
aifd run
# or
aifd run -webui
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


(More)

### Proxy Other Cloud Models

- **Applicable scenarios:** 
  For instance, through [LiteLLM](https://github.com/BerriAI/litellm), you can convert the API format of many cloud models to the OpenAI API format and then use this service as a proxy.

(More)

<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## Configuration

Execute `aifd run --webui` to enter the configuration page (default service address http://localhost:8001).

Detailed configuration descriptions can be seen in the [.env.example](.env.example) file. (To be completed)


### Caching

After enabling caching, the content of specified routes will be cached. The forwarding types are divided into `openai` and `general`, with slightly different behaviors for each.
When using `general` forwarding, by default, the same requests will all be responded to using the cache.
When using `openai` forwarding, after enabling caching, the caching behavior can be controlled through OpenAI's `extra_body` parameter, such as

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

### Custom Api Keys

<details open>
  <summary>Click for more details</summary>


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
    "tools": null,
    "is_tool_calls": false,
    "assistant": "Hello! How can I assist you today?"
  }
]
```


</details>

## Contributions
Feel free to make contributions to this module by submitting pull requests or raising issues in the repository.

## License

OpenAI-Forward is licensed under the [MIT](https://opensource.org/license/mit/) license.
