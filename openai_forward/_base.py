from fastapi import Request, Response, HTTPException, status
from fastapi.responses import StreamingResponse, RedirectResponse, FileResponse, JSONResponse
from loguru import logger
import httpx
from starlette.background import BackgroundTask
import os
from .config import setting_log

setting_log(log_name="openai_forward.log")


class OpenaiBase:
    default_api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com")
    stream_timeout = 20
    timeout = 30
    non_stream_timeout = 30
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

    @classmethod
    async def _reverse_proxy(cls, request: Request):
        client: httpx.AsyncClient = request.app.state.client
        url = httpx.URL(path=request.url.path, query=request.url.query.encode('utf-8'))
        headers = dict(request.headers)
        auth = headers.pop("authorization", None)
        if auth and str(auth).startswith("Bearer sk-"):
            tmp_headers = {'Authorization': auth}
        elif cls.default_api_key:
            auth = "Bearer " + cls.default_api_key
            tmp_headers = {'Authorization': auth}
        else:
            tmp_headers = {}

        headers.pop("host", None)
        headers.pop("user-agent", None)
        headers.update(tmp_headers)

        req = client.build_request(
            request.method, url, headers=headers,
            content=request.stream(),
            timeout=cls.timeout,
        )
        r = await client.send(req, stream=True)

        return StreamingResponse(
            r.aiter_bytes(),
            status_code=r.status_code,
            # headers=r.headers,
            media_type=r.headers.get("content-type"),
            background=BackgroundTask(r.aclose)
        )

    @staticmethod
    def try_get_response(url, method, headers, params, payload, stream, timeout):
        import requests
        if params is None:
            params = {}

        def _exec(time_out):
            if method == 'post':
                return requests.post(url, headers=headers, params=params, json=payload, stream=stream,
                                     timeout=time_out)
            elif method == 'get':
                return requests.get(url, params=params, headers=headers, timeout=time_out)
            else:
                logger.error(f"method {method} not supported")
                raise NotImplementedError

        if stream:
            for i, current_timeout in enumerate([1.5, timeout, 2.5, 2.5, 1.5]):
                try:
                    logger.debug(f"try {i + 1} times, timeout={current_timeout}")
                    return _exec(time_out=current_timeout)
                except:
                    ...
            raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Request Timeout")
        else:
            return _exec(time_out=timeout)

    async def forwarding(self, url, request: Request, params=None, data=None, default_openai_auth=None,
                         non_stream_timeout=None):
        non_stream_timeout = non_stream_timeout or self.non_stream_timeout
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
        response = self.try_get_response(url=url, method=method,
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
