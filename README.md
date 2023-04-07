# OpenAI Forward
## 简介
OpenAI 接口转发服务.   
用途： 
解决国内无法直接访问OpenAI的问题，将该服务部署在海外服务器上，通过该服务转发OpenAI的请求。即搭建反向代理服务
测试地址：http://2.56.125.247:9999/v1/chat/completions  

### 转发接口示例
`https://api.openai.com`
- [x] `/dashboard/billing/usage`
- [x] `/dashboard/billing/credit_grants`
- [x] `/v1/chat/completions`
- [x] `/v1/completions`
- [x] `/v1/models`
- [x] `/v1/models/{model}`


## 服务部署
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
当然也可以将 OPENAI_API_KEY 作为环境变量传入作为默认api key， 这样客户端在请求相关路由时可以无需在Header中传入Authorization。
带默认api key的启动方式：
```bash
OPENAI_API_KEY="sk-xxx" openai_forward run --port=9999 --workers=1
```
注: 如果既存在默认api key又在请求头中传入了api key，则以请求头中的api key会覆盖默认api key.

### Option 2
另一种使用nodejs的部署方式，环境中需已安装node, 优点是默认转发`https://api.openai.com`的所有接口路由，但是不支持设定默认api key。
启动方式
```bash
openai_forward node --port=9999
```

### 方式二: Docker compose
下载项目根目录下的`docker-compose.yaml`文件，然后在文件路径下执行以下命令即可。
```bash
docker-compose up -d
```
注：同样可以在docker-compose.yaml文件中传入环境变量OPENAI_API_KEY=sk-xxx作为默认api key

## 服务调用
替换openai的api地址为该服务的地址即可，如：
```bash
https://api.openai.com/v1/chat/completions
```
替换为
```bash
http://{ip}:{port}/v1/chat/completions
```

个人搭建的代理服务(仅供测试, 不带默认api key):  
http://2.56.125.247:9999/v1/chat/completions  

## 应用
### [chatgpt-web](https://github.com/Chanzhaoyu/chatgpt-web) 
修改 [Docker Compose](https://github.com/Chanzhaoyu/chatgpt-web#docker-compose) 中的`OPENAI_API_BASE_URL`为我们搭建的代理服务地址即可：
```bash
OPENAI_API_BASE_URL: http://2.56.125.247:9999 
```

### [ChatGPT-Next-Web](https://github.com/Yidadaa/ChatGPT-Next-Web)
```bash
docker run -d -p 3000:3000 -e OPENAI_API_KEY="sk-xxx" -e CODE="<your password>" BASE_URL="2.56.125.247:9999" PROTOCOL="http" yidadaa/chatgpt-next-web
```
