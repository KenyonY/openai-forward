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

    def add_allowed_ip(self, ip: str):
        if ip == "*":
            ...
        else:
            self.allow_ips.append(ip)

    def validate_request_host(self, ip):
        if ip == "*" or ip in self.allow_ips:
            return True
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Forbidden, please add {ip=} to `allow_ips`")

    @staticmethod
    def try_get_response(n, url, method, headers, params, payload, stream, timeout):
        if params is None:
            params = {}
        for _ in range(n):
            try:
                if method == 'post':
                    return requests.post(url, headers=headers, params=params, json=payload, stream=stream,
                                         timeout=timeout)
                elif method == 'get':
                    return requests.get(url, params=params, headers=headers, timeout=timeout)
                else:
                    logger.error(f"method {method} not supported")
                    raise NotImplementedError
            except:
                ...
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Request Timeout")

    async def forwarding(self, url, request: Request, params=None, data=None, default_openai_auth=None,
                         non_stream_timeout=30):
        method = request.method.lower()
        if data is not None:
            payload_tmp = data.dict()
            payload = payload_tmp.copy()
            for key, value in payload_tmp.items():
                if value is None:
                    payload.pop(key)
        else:
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
        else:
            if default_openai_auth:
                auth = "Bearer " + default_openai_auth
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
        logger.debug(f"{payload.get('messages')=}")
        # logger.debug(f"{headers=}")
        response = self.try_get_response(n=3, url=url, method=method,
                                         params=params,
                                         headers=headers, payload=payload, stream=stream,
                                         timeout=timeout)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        if stream:
            return StreamingResponse(content=response.iter_content(chunk_size=32),
                                     status_code=response.status_code,
                                     media_type=response.headers.get("content-type"))
        else:
            return Response(content=response.content,
                            status_code=response.status_code,
                            media_type=response.headers.get("content-type"))
