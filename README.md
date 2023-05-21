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



本项目用于解决一些地区无法直接访问OpenAI的问题，将该服务部署在可以正常访问openai
api的服务器上，通过该服务转发OpenAI的请求。即搭建反向代理服务  

---

由本项目搭建的长期代理地址：
> https://api.openai-forward.top  



## 目录

- [功能](#功能)
- [部署指南](#部署指南)
- [应用](#应用)
- [配置选项](#配置选项)
- [聊天日志](#聊天日志)
- [高级配置](#高级配置)

## 功能
**基础功能**  
- [x] 支持转发OpenAI所有接口
- [x] 支持流式响应
- [x] 支持指定转发路由前缀
- [x] docker部署
- [x] pip 安装部署
- [x] vercel 一键个人免费部署
  [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fbeidongjiedeguang%2Fopenai-forward&project-name=openai-forward&repository-name=openai-forward&framework=other)

**高级功能**  
- [x] 实时记录聊天记录(包括流式响应的聊天内容)
- [x] 允许输入多个openai api key 组成轮询池
- [x] 自定义 api key (见高级配置)
- [x] 支持请求IP验证(IP白名单与黑名单)

## 部署指南

提供三种部署方式
1. [vps + pip 安装部署](deploy.md#pip-推荐) (推荐)
2. [vps + Docker](deploy.md#docker-推荐) (推荐) 
    > https://api.openai-forward.top 
3. [一键Vercel部署](deploy.md#vercel-一键部署) 
   > https://vercel.openai-forward.top 

## 应用

### [聊天应用](https://chat.beidongjiedeguang.top)

基于开源项目[ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)搭建自己的chatgpt服务  
替换docker启动命令中的 `BASE_URL`为我们自己搭建的代理服务地址

```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="sk-******" \
    -e BASE_URL="https://api.openai-forward.top" \
    -e CODE="kunyuan" \
    yidadaa/chatgpt-next-web 
``` 
这里部署了一个，供大家轻度使用:  
 https://chat.beidongjiedeguang.top , 访问密码: `kunyuan` 

### 在代码中使用

**JS/TS**

```diff
  import { Configuration } from "openai";
  
  const configuration = new Configuration({
+ basePath: "https://api.openai-forward.top/v1",
  apiKey: "sk-******",
  });
```

**Python**

```diff
  import openai
+ openai.api_base = "https://api.openai-forward.top/v1"
  openai.api_key = "sk-******"
```

**gpt-3.5-turbo**
```bash
curl https://api.openai-forward.top/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-******" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**Image Generation (DALL-E)**
```bash
curl --location 'https://api.openai-forward.top/v1/images/generations' \
--header 'Authorization: Bearer sk-******' \
--header 'Content-Type: application/json' \
--data '{
    "prompt": "A photo of a cat",
    "n": 1,
    "size": "512x512"
}'
```


## 配置选项

**`openai-forward run`参数配置项**

| 配置项       | 说明 | 默认值 |
|-----------| --- | :---: |
| --port    | 服务端口号 | 8000 |
| --workers | 工作进程数 | 1 |

更多参数 `openai-forward run --help` 查看

**环境变量配置项**  
支持从运行目录下的`.env`文件中读取: 

| 环境变量            | 说明                                                              |           默认值            |
|-----------------|-----------------------------------------------------------------|:------------------------:|
| OPENAI_API_KEY  | 默认openai api key，支持多个默认api key, 以 `sk-` 开头， 以空格分割      |            无             |
| FORWARD_KEY     | 允许调用方使用该key代替openai api key，支持多个forward key, 以`fk-` 开头, 以空格分割 |      无             |
| OPENAI_BASE_URL | 转发base url                                                      | `https://api.openai.com` |
| LOG_CHAT        | 是否记录聊天内容                                                        |          `true`          |
| ROUTE_PREFIX    | 路由前缀                                                            |            无             |
| IP_WHITELIST    | ip白名单, 空格分开                                                     |           无            |
| IP_BLACKLIST    | ip黑名单, 空格分开                                                     |           无            | 


## 高级配置

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
curl https://api.openai-forward.top/v1/chat/completions \
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
+ openai.api_base = "https://api.openai-forward.top/v1"
- openai.api_key = "sk-******"
+ openai.api_key = "fk-******"
```
**Web application**
```bash 
docker run -d \
    -p 3000:3000 \
    -e OPENAI_API_KEY="fk-******" \
    -e BASE_URL="https://api.openai-forward.top" \
    -e CODE="<your password>" \
    yidadaa/chatgpt-next-web 
``` 

## 聊天日志

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

## Backer and Sponsor

<a href="https://www.jetbrains.com/?from=beidongjiedeguang/openai-forward" target="_blank">
<img src=".github/images/jetbrains.svg" width="100px" height="100px">
</a>

## License

Openai-forward is licensed under the [MIT](https://opensource.org/license/mit/) license.
