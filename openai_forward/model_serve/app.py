from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
import orjson

from .. import __version__
from .helper import generate, stream_generate_efficient
import os
from loguru import logger


app = FastAPI(title="openai-forward-model-serve", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.middleware("http")
# async def normalize_route(request: Request, call_next):
#     path = request.url.path
#     request.scope["path"] = normalize_route_path(path)
#     response = await call_next(request)
#     return response


@app.get(
    "/healthz",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
def healthz(request: Request):
    return "OK"


class CustomModelManager:
    from .auto_model import AutoModel
    auto_model = AutoModel(
        pretrained_model_name_or_path=os.environ['MODEL_NAME_OR_PATH'],
        device=os.environ['DEVICE'],
        torch_dtype=os.environ['TORCH_DTYPE'],
        attn_implementation=os.environ['ATTN_IMPL'],
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
        payload_model = payload.pop("model", None)

        if stream:
            return StreamingResponse(
                stream_generate_efficient(request,self.call_model_name, self.auto_model.stream_infer, **payload),
                media_type="text/event-stream",
            )
        else:
            return Response(
                content=generate(self.call_model_name, self.auto_model.infer(**payload)),
                media_type="application/json",
            )

model_manager = CustomModelManager()

app.add_route(
    "/v1/chat/completions",
    route=model_manager.chat_completions,
    methods=["POST", "GET"],
)

