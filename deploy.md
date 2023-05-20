# 部署指南

## pip (推荐)

**安装**

```bash
pip install openai-forward
```

**运行转发服务**  
可通过`--port`指定端口号，默认为`8000`

```bash
openai_forward run --port=9999 
```

服务就搭建完成了，使用方式只需将`https://api.openai.com` 替换为服务所在端口`http://{ip}:{port}` 即可。

当然也可以将 OPENAI_API_KEY 作为环境变量或`--api_key`参数传入作为默认api key， 这样客户端在请求相关路由时可以无需在Header中传入Authorization。
带默认api key的启动方式：

```bash
openai_forward run --port=9999 --api_key="sk-******"
```

注: 如果既存在默认api key又在请求头中传入了api key，则以请求头中的api key会覆盖默认api key.


### 服务调用

替换openai的api地址为该服务的地址即可，如：

```bash
https://api.openai.com/v1/chat/completions
```

替换为

```bash
http://{ip}:{port}/v1/chat/completions
```
## 开启SSL
常用方式是使用nginx 代理转发 openai-forward 服务端口(9999)至443端口。需要注意的是，若要使用流式转发，在nginx配置中需要取消缓存操作：
   ```bash
    proxy_cache off; 
    proxy_buffering off; 
    chunked_transfer_encoding on; 
    tcp_nopush on;  
    tcp_nodelay on;  
    keepalive_timeout 300;  
```

## Docker (推荐)

```bash
docker run -d -p 9999:8000 beidongjiedeguang/openai-forward:latest 
```

将映射宿主机的9999端口，通过`http://{ip}:9999`访问服务。  
注：同样可以在启动命令中通过-e传入环境变量OPENAI_API_KEY=sk-xxx作为默认api key



## 源码部署

```bash
git clone https://github.com/beidongjiedeguang/openai-forward.git --depth=1
cd openai-forward

pip install -e .
openai-forward run 
```

## Vercel 一键部署


[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fbeidongjiedeguang%2Fopenai-forward&project-name=openai-forward&repository-name=openai-forward&framework=other)  
1. 点击按钮即可一键免费部署  
也可fork本次仓库，再手动在vercel操作界面import项目
2. [绑定自定义域名](https://vercel.com/docs/concepts/projects/domains/add-a-domain)：Vercel 分配的域名 DNS 在某些区域被污染了导致国内无法访问，绑定自定义域名即可直连。

⚠️目前Vercel中使用Serverless Function部署的方式尚不支持流式，没有Log记录, 而且仅提供较短的接口超时时间。
所以如果重度使用并不推荐。  

> https://vercel.openai-forward.top  
这里是使用Vercel一键部署的服务，仅供测试

