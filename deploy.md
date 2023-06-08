
<h1 align="center">
    <br>
    部署指南
    <br>
</h1>
<div align="center">

[pip部署](#pip部署) |
[docker部署](#docker部署) |
[cloudflare部署](#cloudflare-部署) |
[railway一键部署](#railway-一键部署) |
[render一键部署](#render-一键部署)

</div>

## pip部署

**安装**

```bash
pip install openai-forward
```

**运行服务**  

```bash
openai_forward run 
```
服务就搭建完成了。  
配置见[配置](README.md#配置选项)

### 服务调用

使用方式只需将`https://api.openai.com` 替换为服务所在端口`http://{ip}:{port}` 就可以了。  
比如
```bash
# 默认
https://api.openai.com/v1/chat/completions
#替换为
http://{ip}:{port}/v1/chat/completions
```

更多使用方式见 [应用](README.md#应用)

### 开启SSL (以https访问域名)
首先准备好一个域名, 如本项目中使用的域名为`api.openai-forward.com`

常用方式是使用nginx(不习惯用命令行配置的话可以考虑用 [Nginx Proxy Manager](https://github.com/NginxProxyManager/nginx-proxy-manager)) 代理转发 openai-forward 服务端口(默认8000)。  
需要注意的是，若要使用流式转发，在nginx配置中需要添加取消代理缓存的配置：
   ```bash
    proxy_cache off; 
    proxy_buffering off; 
```

然后就可以https访问了。


## Docker部署

```bash
docker run -d -p 9999:8000 beidongjiedeguang/openai-forward:latest 
```

将映射宿主机的9999端口，通过`http://{ip}:9999`访问服务。  

注：同样可以在启动命令中通过-e传入环境变量OPENAI_API_KEY=sk-xxx作为默认api key  
启用SSL同上.
环境变量配置见[环境变量配置](README.md#环境变量配置项)


## 源码部署

```bash
git clone https://github.com/beidongjiedeguang/openai-forward.git --depth=1
cd openai-forward

pip install -e .
openai-forward run 
```
启用SSL同上.

---

## ~~Vercel 一键部署~~

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fbeidongjiedeguang%2Fopenai-forward&project-name=openai-forward&repository-name=openai-forward&framework=other)  
⚠️目前Vercel中使用Serverless Function部署的方式尚不支持流式，没有Log记录, 而且仅提供较短的接口超时时间。
所以现在不推荐使用这种部署方式。 (部署时需将环境变量`LOG_CHAT` 设置为`False`,否则会部署/运行失败。)

1. 点击按钮即可一键免费部署  
也可先fork本仓库，再手动在vercel操作界面import项目
2. [绑定自定义域名](https://vercel.com/docs/concepts/projects/domains/add-a-domain)：Vercel 分配的域名 DNS 在某些区域被污染了导致国内无法访问，绑定自定义域名即可直连。


> https://vercel.openai-forward.com  
仅供测试

---

## Cloudflare 部署

部署方式二选一： 
* Pages部署: fork本仓库，在[cloudflare](https://dash.cloudflare.com/)上创建应用程序时选择Pages, 然后选择连接到Git, 选择刚刚fork的仓库即可完成部署。  
* Workers部署: 在[cloudflare](https://dash.cloudflare.com/)上创建应用程序时选择Workers, 部署好示例代码后，点击快速修改（quick edit）复制[_worker.js](_worker.js) 至代码编辑器即可完成服务部署。    

绑定自定义域名: cloudflare自动分配的域名国内也无法访问，所以也需要绑定自定义域名.

绑定自定义域名需要将域名默认nameserver(域名服务器)绑定到cloudflare提供的nameserver，大体上过程是：
```mermaid
stateDiagram-v2
    [*] --> 注册cloudflare
    [*] --> 在任意机构注册域名
    注册cloudflare --> 添加worker/page
    添加worker/page --> 在cloudflare的worker/page中添加域名 : worker/page应用部署成功
    在任意机构注册域名 --> 去注册域名机构更改默认nameserver为cloudflare提供的nameserver
    去注册域名机构更改默认nameserver为cloudflare提供的nameserver --> 在cloudflare的worker/page中添加域名: 域名服务器更改验证成功
    在cloudflare的worker/page中添加域名 --> 成功 
```
这种部署方式轻便简洁，支持流式转发. 对于没有vps的用户还是十分推荐的。不过目前[_worker.js](_worker.js)这个简单脚本仅提供转发服务, 不提供额外功能。

> https://cloudflare.worker.openai-forward.com  
> https://cloudflare.page.openai-forward.com  

---

## Railway 一键部署
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/tejCum?referralCode=U0-kXv)

1. 点击上面部署按钮进行一键部署  
   也可先fork本仓库，再手动在操作界面导入自己的fork项目
2. 填写环境变量，必填项`PORT` :`8000`, 可选项 如默认的OPENAI_API_KEY 等
3. 绑定自定义域名

注： Railway 每月提供 $5.0和500小时执行时间的免费计划。这意味着单个免费用户每个月只能使用大约21天

> https://railway.openai-forward.com

---

## Render 一键部署
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/beidongjiedeguang/openai-forward)

体验下来，Render应该算是所有部署中最简易的一种, 并且它生成的域名国内可以直接访问！

1. 点击一键部署按钮  
   如果提示需要绑定卡，则可先fork本仓库 -->到Render的Dashboard上 New Web Services --> Connect 到刚刚fork到仓库
2. 填写环境变量，如默认的OPENAI_API_KEY 等,也可以不填

然后等待部署完成即可。  
Render的免费计划: 每月750小时免费实例时间(意味着单个实例可以不间断运行)、100G带宽流量、500分钟构建时长.

注：默认render在15分钟内没有服务请求时会自动休眠(好处是休眠后不会占用750h的免费实例时间)，休眠后下一次请求会被阻塞 5~10s。
若不希望服务15分钟自动休眠，可以使用定时脚本（如每14分钟）去请求服务进行保活。
如果希望零停机部署可以在设置中设置`Health Check Path`为`/docs` 
> https://render.openai-forward.com  
> https://openai-forward.onrender.com 


