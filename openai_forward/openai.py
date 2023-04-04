from ._base import OpenaiBase, Request
from .routers.schemas import OpenAIV1ChatCompletion
from dotenv import load_dotenv
import os

load_dotenv()


class Openai(OpenaiBase):
    def __init__(self):
        self.defualt_auth = os.environ.get("OPENAI_API_KEY", "")

    async def _forward(self, route: str, request: Request, data=None, validate_host=False, non_stream_timeout=30):
        url = os.path.join(self.base_url, route)
        if validate_host:
            self.validate_request_host(request.client.host)
        return await self.forwarding(url,
                                     request,
                                     data,
                                     default_openai_auth=self.defualt_auth,
                                     non_stream_timeout=non_stream_timeout)

    async def credit_grants(self, request: Request):
        url = os.path.join(self.base_url, "dashboard/billing/credit_grants")
        return await self.forwarding(url, request=request, non_stream_timeout=3,
                                     default_openai_auth=self.defualt_auth)

    async def billing_usage(self, params: dict, request: Request):
        url = os.path.join(self.base_url, "dashboard/billing/usage")
        return await self.forwarding(url, request=request, params=params, non_stream_timeout=3,
                                     default_openai_auth=self.defualt_auth)

    async def v1_chat_completions(self, data: OpenAIV1ChatCompletion, request: Request, validate_host=False):
        return await self._forward("v1/chat/completions", request, data, validate_host)

    async def v1_list_models(self, request: Request, validate_host=False):
        return await self._forward("v1/models", request, data=None, validate_host=validate_host, non_stream_timeout=3)

    async def retrive_model(self, request: Request, model: str, validate_host=False):
        return await self._forward(f"v1/models/{model}", request, data=None, validate_host=validate_host,
                                   non_stream_timeout=3)

    async def v1_completions(self, data, request: Request, validate_host=False):
        return await self._forward("v1/completions", request, data=data, validate_host=validate_host)

    async def v1_edits(self, data, request: Request, validate_host=False):
        return await self._forward("v1/edits", request, data=data, validate_host=validate_host)

    async def v1_image_generations(self, data, request: Request, validate_host=False):
        return await self._forward("v1/images/generations", request, data=data, validate_host=validate_host)

    async def v1_embeddings(self, data, request: Request, validate_host=False):
        return await self._forward("v1/embeddings", request, data=data, validate_host=validate_host)

    # async def v1_audio_transcriptions(self, data, request: Request, validate_host=False):
    #     return await self._forward("audio/transcriptions", request, data=data, validate_host=validate_host)

    async def v1_fine_tunes(self, data, request: Request, validate_host=False):
        return await self._forward("v1/fine-tunes", request, data=data, validate_host=validate_host)

    async def v1_retrieve_fine_tunes(self, path_var, request: Request, validate_host=False):
        return await self._forward(f"v1/fine-tunes/{path_var}", request, validate_host=validate_host)
