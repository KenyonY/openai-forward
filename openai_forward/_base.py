from fastapi import Request, Response, HTTPException, status
from fastapi.responses import StreamingResponse, RedirectResponse, FileResponse, JSONResponse
import requests
from loguru import logger
from .config import setting_log

setting_log(log_name="openai_forward.log")


class OpenaiBase:
    base_url = "https://api.openai.com"
    stream_timeout = 1.5
    allow_ips = []

    def set_request_ip(self, ip: str):
        if ip == "*":
            ...
        else:
            self.allow_ips.append(ip)

    def validate_request_host(self, ip):
        if ip == "*" or ip in self.allow_ips:
            return True
        else:
            return False

    @staticmethod
    def try_get_response(n, url, method, headers, payload, stream, timeout):
        for _ in range(n):
            try:
                if payload:
                    return requests.request(method, url, headers=headers, json=payload, stream=stream, timeout=timeout)
                else:
                    return requests.request(method, url, headers=headers, timeout=timeout)
            except:
                ...
        return False

    async def forwarding(self, url, request: Request, default_openai_auth=None, non_stream_timeout=30):
        method = request.method.lower()
        try:
            payload = await request.json()
        except:
            payload = {}
        stream = payload.get('stream')
        timeout = self.stream_timeout if stream else non_stream_timeout

        geted_headers = dict(request.headers)
        posted_auth = geted_headers.get("authorization")
        if posted_auth and str(posted_auth).startswith("Bearer sk-"):
            auth = posted_auth
            # logger.info(f"auth from request: {auth}")
        else:
            if default_openai_auth:
                auth = default_openai_auth
            else:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={
                    "error": {
                        "message": "You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY), or as the password field (with blank username) if you're accessing the API from your browser and are prompted for a username and password. You can obtain an API key from https://platform.openai.com/account/api-keys.",
                        "type": "invalid_request_error",
                        "param": None,
                        "code": None
                    }
                })
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth
        }
        logger.debug(f"{payload.get('messages')}")

        response = self.try_get_response(3, url, method=method, headers=headers, payload=payload, stream=stream,
                                         timeout=timeout)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        if stream:
            return StreamingResponse(response.iter_content(chunk_size=32),
                                     media_type=response.headers.get("content-type"))
        else:
            return Response(content=response.content, status_code=response.status_code, headers=response.headers)
