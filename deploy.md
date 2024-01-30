
<h1 align="center">
    <br>
    部署指南
    <br>
</h1>
<div align="center">

一键部署至render   
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/KenyonY/openai-forward)



[pip部署](#pip部署) |
[docker部署](#docker部署) |
[render一键部署](#render-一键部署) 

</div>

**本地部署**

1. [pip 安装部署](deploy.md#pip部署)
2. [Docker部署](deploy.md#docker部署)

**一键免费云平台部署**

1. [Render一键部署](deploy.md#render-一键部署)
2. 更多部署： https://github.com/KenyonY/openai-forward/blob/0.5.x/deploy.md

**其它反代**  
[CloudFlare AI Gateway](https://developers.cloudflare.com/ai-gateway/get-started/creating-gateway/)  
[ChatGPT](https://github.com/pandora-next/deploy)  


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

## Render 一键部署
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/KenyonY/openai-forward)

Render应该算是所有部署中最简易的一种, 并且它生成的域名国内可以直接访问！

1. 点击一键部署按钮  
   也可先fork本仓库 -->到Render的Dashboard上 New Web Services --> Connect 到刚刚fork到仓库 后面步骤均默认即可
2. 填写环境变量，`openai-forward`所有配置都可以通过环境变量设置，可以根据自己需要填写。

然后等待部署完成即可。  
Render的免费计划: 每月750小时免费实例时间(意味着单个实例可以不间断运行)、100G带宽流量、500分钟构建时长.

注：默认render在15分钟内没有服务请求时会自动休眠(好处是休眠后不会占用750h的免费实例时间)，休眠后下一次请求会被阻塞 ~15s。
如果希望服务15分钟不自动休眠，可以使用定时脚本（如每14分钟）对render服务进行保活。保活脚本参考`scripts/keep_render_alive.py`.    
如果希望零停机部署可以在render设置中配置 `Health Check Path`为`/healthz`   

> https://render.openai-forward.com  
> https://openai-forward.onrender.com 

