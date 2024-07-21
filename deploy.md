
<h1 align="center">
    <br>
    部署指南
    <br>
</h1>
<div align="center">



[pip部署](#pip部署) |
[docker部署](#docker部署) 

</div>

**本地部署**

1. [pip 安装部署](deploy.md#pip部署)
2. [Docker部署](deploy.md#docker部署)

**~~一键免费云平台部署~~**

1. ~~[Render一键部署](deploy.md#render-一键部署)~~
2. ~~更多部署： https://github.com/KenyonY/openai-forward/blob/0.5.x/deploy.md~~

**其它反代**  
[CloudFlare AI Gateway](https://developers.cloudflare.com/ai-gateway/get-started/creating-gateway/)  
~~[ChatGPT](https://github.com/pandora-next/deploy)~~


---
## pip部署

**安装**

```bash
pip install openai-forward
```

**运行服务**  

```bash
aifd run   
```
或运行webui
```bash
aifd run --webui
```
服务就搭建完成了。  
配置见[配置](README.md#配置)

### 服务调用

使用方式只需将`https://api.openai.com` 替换为服务所在端口`http://{ip}:{port}`   
如
```bash
# 默认
https://api.openai.com/v1/chat/completions
#替换为
http://{ip}:{port}/v1/chat/completions
```


### 开启SSL (以https访问域名)
首先准备好一个域名, 如本项目中使用的域名为`api.openai-forward.com`

常用方式是使用nginx(不习惯用命令行配置的话可以考虑用 [Nginx Proxy Manager](https://github.com/NginxProxyManager/nginx-proxy-manager), 它可方便设置Let's Encrypt证书自动申请和自动续期) 
或 [Caddy](https://caddyserver.com/docs/) 进行代理转发 openai-forward 服务端口(默认8000) 至https端口。  
需要注意的是，若要使用流式转发，在nginx配置中需要添加关闭代理缓存的配置, 即在Nginx Proxy Manager页面的 Custom Nginx Configuration中写入：
```bash
proxy_buffering off;
```

<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## Docker部署

```bash
docker run -d -p 8000:8000 beidongjiedeguang/openai-forward:latest 
```

如果指定 `.env` 环境变量则：

```bash
docker run --env-file .env -d -p 8000:8000 beidongjiedeguang/openai-forward:latest 
```

将映射宿主机的8000端口，通过`http://{ip}:8000`访问服务。  
容器内日志路径为`/home/openai-forward/Log/`, 可在启动时将其映射出来。  

启用SSL同上.
环境变量配置见[环境变量配置](README.md#配置)


## 源码部署

```bash
git clone https://github.com/KenyonY/openai-forward.git --depth=1
cd openai-forward

pip install -e .
aifd run 
```
启用SSL同上.


<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>
