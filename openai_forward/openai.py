from ._base import OpenaiBase, Request
import os


class Openai(OpenaiBase):
    def __init__(self):
        self.defualt_auth = os.environ.get("OPENAI_API_KEY", None)

    async def credit_grants(self, request: Request):
        url = os.path.join(self.base_url, "dashboard/billing/credit_grants")
        return await self.forwarding(url, request, non_stream_timeout=5, default_openai_auth=self.defualt_auth)

    async def completions(self, request: Request, validate_host=False):
        url = os.path.join(self.base_url, "v1/chat/completions")
        if validate_host:
            self.validate_request_host(request.client.host)
        return await self.forwarding(url, request, default_openai_auth=self.defualt_auth)
