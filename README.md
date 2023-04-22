[**中文**](./README_ZH.md) | **English**

<h1 align="center">
    <br>
    OpenAI Forward
    <br>
</h1>
<p align="center">
    <b> OpenAI API 接口转发服务 <br/>
    The fastest way to deploy openai api forward proxy </b>
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

</p>
This project is designed to solve the problem of some regions being unable to directly access OpenAI. The service is deployed on a server that can access the OpenAI API, and OpenAI requests are forwarded through the service, i.e. a reverse proxy service is set up. 

Test access: https://caloi.top/v1/chat/completions is equivalent to https://api.openai.com/v1/chat/completions 

# Table of Contents 

- [Features](#Features) 
- [Usage](#Usage) 
- [Service Deployment](#Service-Deployment) 
- [Service Usage](#Service Usage) 

# Features 
- [x] Supports forwarding of all OpenAI interfaces 
- [x] Supports request IP verification 
- [x] Supports streaming forwarding 
- [x] Supports default API key 
- [x] pip installation and deployment 
- [x] Docker deployment 
- [ ] Chat content security: Chat content streaming filtering 

# Usage 
> Here, the proxy address set up by the individual, https://caloi.top, is used as an example 

### Image Generation (DALL-E):
```bash 
curl --location 'https://caloi.top/v1/images/generations' \ 
--header 'Authorization: Bearer sk-******' \ 
--header 'Content-Type: application/json' \ 
--data '{ 
    "prompt": "A photo of a cat", 
    "n": 1, 
    "size": "512x512"
}' 
``` 

### [chatgpt-web](https://github.com/Chanzhaoyu/chatgpt-web) 
Modify the `OPENAI_API_BASE_URL` in [Docker Compose](https://github.com/Chanzhaoyu/chatgpt-web#docker-compose) to the address of the proxy service we set up: 
```bash 
OPENAI_API_BASE_URL: https://caloi.top 
``` 

### [ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web) 
Replace `BASE_URL` in the docker startup command with the address of the proxy service we set up: 
```bash 
docker run -d -p 3000:3000 -e OPENAI_API_KEY="sk-******" -e CODE="<your password>" -e BASE_URL="caloi.top" yidadaa/chatgpt-next-web 
``` 


### Using in a module 

**Used in JS/TS** 
```typescript 
import { Configuration } from "openai"; 

const configuration = new Configuration({ 
    basePath: "https://caloi.top", 
    apiKey: "sk-******", 

}); 
``` 
**Used in Python** 
```python 
import openai 
openai.api_base = "https://caloi.top" 
openai.api_key = "sk-******" 
``` 

# Service Deployment 
Two service deployment methods are provided, choose one 

## Method 1: pip 
**Installation** 
```bash 
pip install openai-forward 
``` 
**Run forwarding service** 
The port number can be specified through `--port`, which defaults to `8000`, and the number of worker processes can be specified through `--workers`, which defaults to `1`. 
```bash 
openai_forward run --port=9999 --workers=1 
``` 
The service is now set up, and the usage is to replace `https://api.openai.com` with the port number of the service `http://{ip}:{port}`. 

Of course, OPENAI_API_KEY can also be passed in as an environment variable as the default API key, so that the client does not need to pass in the Authorization in the header when requesting the relevant route. 
Startup command with default API key: 
```bash 
OPENAI_API_KEY="sk-xxx" openai_forward run --port=9999 --workers=1 
``` 
Note: If both the default API key and the API key passed in the request header exist, the API key in the request header will override the default API key. 

## Method 2: Docker (recommended) 
```bash 
docker run --name="openai-forward" -d -p 9999:8000 beidongjiedeguang/openai-forward:latest 
``` 
The 9999 port of the host is mapped, and the service can be accessed through `http://{ip}:9999`. 
Note: You can also pass in the environment variable OPENAI_API_KEY=sk-xxx as the default API key in the startup command. 

# Service Usage 
Simply replace the OpenAI API address with the address of the service we set up, such as: 
```bash 
https://api.openai.com/v1/chat/completions 
``` 
Replace with 
```bash 
http://{ip}:{port}/v1/chat/completions 
```