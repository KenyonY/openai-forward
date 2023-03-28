# Openai forwarding agent
## 简介
openai 接口转发服务.   
用途： 
解决国内无法直接访问openai的问题，将该服务部署在海外服务器上，通过该服务转发openai的请求。即搭建反向代理服务

### 已实现转发的接口
`https://api.openai.com`

- [x] `/v1/chat/completions`
- [x] `/dashboard/billing/credit_grants`


## 服务部署
### 方式一: 使用 pip
**Install**
```bash
pip install openai-forward
```
**Run**
```bash
openai_forward run --port 8000 --worders=1
```

### 方式二: 使用Docker compose
下载项目根目录下的`docker-compose.yaml`文件，然后在文件路径下执行以下命令即可。
```bash
docker-compose up -d
```

## 服务调用
替换openai的api地址为该服务的地址即可，如：
```bash
https://api.openai.com/v1/chat/completions
```
替换为
```bash
http://{ip}:{port}/v1/chat/completions
```

个人搭建的代理服务(仅供测试):  
http://2.56.125.247:9999/v1/chat/completions  
http://2.56.125.247:9999/dashboard/billing/credit_grants 

