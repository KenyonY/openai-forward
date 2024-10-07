from fastapi import Request
from fastapi.responses import Response, StreamingResponse
import orjson
import os
from loguru import logger

from .helper import generate, stream_generate_efficient
from ..backend.transformers_backend import AutoModel
from ..backend.vllm_backend import VllmEngine
# from ..backend.misc import get_current_device


class CustomModelManager:
    # auto_model = AutoModel(
    #     pretrained_model_name_or_path=os.environ['MODEL_NAME_OR_PATH'],
    #     device=os.environ['DEVICE'],
    #     torch_dtype=os.environ['TORCH_DTYPE'],
    #     attn_implementation=os.environ['ATTN_IMPL'],
    # )

    auto_model = VllmEngine(
        pretrained_model_name_or_path=os.environ['MODEL_NAME_OR_PATH'],
        quantization=os.environ.get('VLLM_QUANTIZATION') or None,
        # max_model_len=int(os.environ['VLLM_MAX_MODEL_LEN']),
        max_num_seqs=int(os.environ['VLLM_MAX_NUM_SEQS']),
        enable_prefix_caching=os.environ['VLLM_ENABLE_PREFIX_CACHING'].lower() == "true",
    )
    call_model_name = os.environ['CALL_MODEL_NAME']

    async def chat_completions(self, request: Request):
        data = await request.body()
        if data:
            payload = orjson.loads(data)
        else:
            payload = {}
        logger.info(f"payload: {payload}")

        stream = payload.get("stream", False)
        assert "messages" in payload

        payload.pop("model", None)

        if stream:
            return StreamingResponse(
                stream_generate_efficient(request, self.call_model_name, self.auto_model.stream_infer, **payload),
                media_type="text/event-stream",
            )
        else:
            return Response(
                content=generate(self.call_model_name, await self.auto_model.infer(**payload)),
                media_type="application/json",
            )
