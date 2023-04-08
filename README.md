# OpenAI Forward
## 简介
OpenAI 接口转发服务.   
用途： 
解决国内无法直接访问OpenAI的问题，将该服务部署在海外服务器上，通过该服务转发OpenAI的请求。即搭建反向代理服务  
测试地址：https://caloi.top/v1/chat/completions 

### 转发接口示例
`https://api.openai.com`
- [x] `/dashboard/billing/usage`
- [x] `/v1/chat/completions`
- [x] `/v1/completions`
- [x] ......

默认转发所有接口。

## 应用
> 这里以个人搭建好的代理地址 https://caloi.top 为例
### [chatgpt-web](https://github.com/Chanzhaoyu/chatgpt-web)
修改 [Docker Compose](https://github.com/Chanzhaoyu/chatgpt-web#docker-compose) 中的`OPENAI_API_BASE_URL`为我们搭建的代理服务地址即可：
```bash
OPENAI_API_BASE_URL: https://caloi.top 
```

### [ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)
```bash
docker run -d -p 3000:3000 -e OPENAI_API_KEY="sk-xxx" -e CODE="<your password>" -e BASE_URL="caloi.top" yidadaa/chatgpt-next-web
```

## 服务搭建
提供两种服务部署方式,选择一种即可

### 方式一:  pip
**安装**
```bash
pip install openai-forward
```
**运行转发服务**  
### Option 1
可通过`--port`指定端口号，默认为`9999`，可通过`--workers`指定工作进程数，默认为`1`
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

### Option 2
另一种使用nodejs的部署方式，环境中需已安装node, 也是默认转发`https://api.openai.com`的所有接口路由，但目前不支持设定默认api key。
启动方式
```bash
openai_forward node --port=9999
```

### 方式二: Docker 
```bash
docker run -itd -p 9999:9999 beidongjiedeguang/openai-forward:latest --port=9999 --workers=1
```
注：同样可以在启动命令中通过-e传入环境变量OPENAI_API_KEY=sk-xxx作为默认api key

## 服务调用
替换openai的api地址为该服务的地址即可，如：
```bash
https://api.openai.com/v1/chat/completions
```
替换为
```bash
http://{ip}:{port}/v1/chat/completions
```

