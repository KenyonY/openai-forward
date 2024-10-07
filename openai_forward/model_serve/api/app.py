from fastapi import FastAPI, Request, status, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from ... import __version__
from ...helper import normalize_route as normalize_route_path
from .manager import CustomModelManager

app = FastAPI(title="openai-forward-model-serve", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def normalize_route(request: Request, call_next):
    path = request.url.path
    request.scope["path"] = normalize_route_path(path)
    response = await call_next(request)
    return response


@app.get(
    "/healthz",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
def healthz(request: Request):
    return "OK"


model_manager = CustomModelManager()


@app.post("/v1/chat/completions",
          response_model=dict,
          status_code=status.HTTP_200_OK,
          # dependencies=[Depends(verify_api_key)],
          )
async def create_chat_completions(request: Request):
    try:
        return await model_manager.chat_completions(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.add_route(
    "/v1/chat/completions",
    route=model_manager.chat_completions,
    methods=["POST", "GET"],
)
