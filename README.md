[**中文**](./README_ZH.md) | **English**

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
This project is designed to solve the problem of some regions being unable to directly access OpenAI. The service is deployed on a server that can access the OpenAI API, and OpenAI requests are forwarded through the service, i.e. a reverse proxy service is set up. 

Test access: https://caloi.top/openai/v1/chat/completions is equivalent to https://api.openai.com/v1/chat/completions  
Or, to put it another way, https://caloi.top/openai is equivalent to https://api.openai.com.

# Table of Contents

- [Features](#Features)
- [Usage](#Usage)
- [Deploy](#Deploy)
- [Service Usage](#Service-Usage)
- [Configuration](#Configuration)
- [Chat Log](#Chat-log)

# Features

- [x] Supports forwarding of all OpenAI interfaces
- [x] Request IP verification
- [x] Streaming Response
- [x] Supports default API key (cyclic call with multiple API keys)
- [x] pip installation and deployment
- [x] Docker deployment
- [x] Support for multiple worker processes
- [x] Support for specifying the forwarding routing prefix

# Usage

> Here, the proxy address set up by the individual, https://caloi.top/openai, is used as an example

### Using in a module


**Python**

```diff
  import openai
+ openai.api_base = "https://caloi.top/openai/v1"
  openai.api_key = "sk-******"
```

**JS/TS**

```diff
  import { Configuration } from "openai";
  
  const configuration = new Configuration({
+ basePath: "https://caloi.top/openai/v1",
  apiKey: "sk-******",
  });
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

Modify the `OPENAI_API_BASE_URL` in [Docker Compose](https://github.com/Chanzhaoyu/chatgpt-web#docker-compose) to the
address of the proxy service we set up:

```bash 
OPENAI_API_BASE_URL: https://caloi.top/openai 
``` 

### [ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)

Replace `BASE_URL` in the docker startup command with the address of the proxy service we set up:

```bash 
docker run -d -p 3000:3000 -e OPENAI_API_KEY="sk-******" -e CODE="<your password>" -e BASE_URL="caloi.top/openai" yidadaa/chatgpt-next-web 
``` 


# Deploy

Two deployment methods are provided, just choose one.

## Use `pip`  (recommended)

**Installation**

```bash 
pip install openai-forward 
``` 

**Run forwarding service**
The port number can be specified through `--port`, which defaults to `8000`, and the number of worker processes can be
specified through `--workers`, which defaults to `1`.

```bash 
openai_forward run --port=9999 --workers=1 
``` 

The service is now set up, and the usage is to replace `https://api.openai.com` with the port number of the
service `http://{ip}:{port}`.

Of course, OPENAI_API_KEY can also be passed in as an environment variable as the default API key, so that the client
does not need to pass in the Authorization in the header when requesting the relevant route.
Startup command with default API key:

```bash 
OPENAI_API_KEY="sk-xxx" openai_forward run --port=9999 --workers=1 
``` 

Note: If both the default API key and the API key passed in the request header exist, the API key in the request header
will override the default API key.

## Use Docker

```bash 
docker run --name="openai-forward" -d -p 9999:8000 beidongjiedeguang/openai-forward:latest 
``` 

The 9999 port of the host is mapped, and the service can be accessed through `http://{ip}:9999`.
Note: You can also pass in the environment variable OPENAI_API_KEY=sk-xxx as the default API key in the startup command.

# Service Usage

Simply replace the OpenAI API address with the address of the service we set up, such as `Chat Completion`
```bash 
https://api.openai.com/v1/chat/completions 
``` 

Replace with

```bash 
http://{ip}:{port}/v1/chat/completions 
```

# Configuration

**`openai-forward run` Parameter Configuration Options**

| Configuration Option | Description | Default Value |
|-----------| --- | :---: |
| --port    | Service port number | 8000 |
| --workers | Number of worker processes | 1 |

**Environment Variable Configuration Options**  
refer to the `.env` file in the project root directory

| Environment Variable  | Description | Default Value |
|-----------------|------------|:------------------------:|
| OPENAI_API_KEY  | Default API key, supports multiple default API keys separated by space. | None |
| OPENAI_BASE_URL | Forwarding base URL | `https://api.openai.com` |
|LOG_CHAT| Whether to log chat content | `true` |
|ROUTE_PREFIX| Route prefix | None |
| IP_WHITELIST    | IP whitelist, separated by space. | None |
| IP_BLACKLIST    | IP blacklist, separated by space. | None |

# Chat Log
The saved path is in the `Log/` directory under the current directory.  
The chat log starts with `chat_` and is written to the file every 5 rounds by default.  
The recording format is as follows:
```text
{'host': xxx, 'model': xxx, 'message': [{'user': xxx}, {'assistant': xxx}]}
{'assistant': xxx}

{'host': ...}
{'assistant': ...}

...
```