
<h1 align="center">
    <br>
    Deployment Guide
    <br>
</h1>
<div align="center">

Deploy with one click to Render   
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/KenyonY/openai-forward)

[pip Deployment](#pip-deployment) |
[docker Deployment](#docker-deployment) |
[Render One-click Deployment](#render-one-click-deployment) 

</div>

This document offers several deployment methods:  
**Local Deployment**

1. [Deployment via pip](#pip-deployment)
2. [Deployment with Docker](#docker-deployment)

**One-click Free Cloud Deployment**

1. [Render One-click Deployment](#render-one-click-deployment)
2. [CloudFlare AI Gateway](https://developers.cloudflare.com/ai-gateway/)
3. More Deployment: https://github.com/KenyonY/openai-forward/blob/0.5.x/deploy.md

---
## pip Deployment

**Installation**

```bash
pip install openai-forward
```

**Run the Service**  

```bash
aifd run   
```
The service is now set up.  
Configuration can be found [here](README_EN.md#configuration).

### Service Invocation

To use, simply replace `https://api.openai.com` with the service port `http://{ip}:{port}`   
For example:
```bash
# Default
https://api.openai.com/v1/chat/completions
# Replace with
http://{ip}:{port}/v1/chat/completions
```


### Enable SSL (to access the domain via https)
First, prepare a domain, such as the one used in this project: `api.openai-forward.com`.

A common method is to use nginx (if you're not familiar with command-line configuration, you might consider [Nginx Proxy Manager](https://github.com/NginxProxyManager/nginx-proxy-manager), which facilitates setting up Let's Encrypt certificates with automatic application and renewal) 
or [Caddy](https://caddyserver.com/docs/) to proxy forward the openai-forward service port (default 8000) to the HTTPS port.  
Note that if you want to use streaming forwarding, you need to add a configuration to disable proxy caching in nginx, i.e., input in Nginx Proxy Manager's Custom Nginx Configuration:
```bash
proxy_buffering off;
```

<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## Docker Deployment

```bash
docker run -d -p 8000:8000 beidongjiedeguang/openai-forward:latest 
```

If the `.env` environment variable is specified:

```bash
docker run --env-file .env -d -p 8000:8000 beidongjiedeguang/openai-forward:latest 
```

This will map the host's 8000 port. Access the service via `http://{ip}:8000`.  
The log path inside the container is `/home/openai-forward/Log/`. It can be mapped when starting up.

Note: For SSL setup, refer to the above. Environment variable configuration can be found [here](README_EN.md#configuration).

## Source Code Deployment

```bash
git clone https://github.com/KenyonY/openai-forward.git --depth=1
cd openai-forward

pip install -e .
aifd run 
```
For SSL setup, refer to the above.

<a>
   <img src="https://raw.githubusercontent.com/KenyonY/openai-forward/main/.github/images/separators/aqua.png" height=8px width="100%">
</a>

## Render One-click Deployment
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/KenyonY/openai-forward)

Render might be considered the easiest of all deployment methods, and the domain it generates can be directly accessed domestically!

1. Click the one-click deployment button.  
   Alternatively, first fork this repository -> Go to Render's Dashboard -> New Web Services -> Connect to the recently forked repository. Follow the default steps thereafter.
2. Fill in the environment variables. All `openai-forward` configurations can be set via environment variables. Set them based on your needs.

Wait for the deployment to complete.  
Render's free plan: 750 hours of free instance time each month (meaning a single instance can run continuously), 100G bandwidth, and 500 minutes of build duration.

Note: By default, Render will automatically go to sleep if there are no service requests within 15 minutes (the advantage is that once asleep, it won't count towards the 750h of free instance time). The next request after it goes to sleep will be blocked for ~15s. If you want the service not to go to sleep after 15 minutes, you can use a timer script (like every 14 minutes) to keep the Render service alive. Refer to the `scripts/keep_render_alive.py` for the keep-alive script.  
For zero-downtime deployments, configure the `Health Check Path` in Render settings to `/healthz`.

> https://render.openai-forward.com  
> https://openai-forward.onrender.com 

--- 

This is a translated version. Make sure to review and adjust any sections as necessary to fit your specific context or technical requirements.