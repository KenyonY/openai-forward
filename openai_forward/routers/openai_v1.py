from ..openai import Openai
from .schemas import OpenAIV1ChatCompletion
from fastapi import Request, APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1", tags=["v1"])
openai = Openai()


@router.get("/models")
async def list_models(request: Request):
    return await openai.v1_list_models(request)


@router.get("/models/{model}")
async def retrive_model(model: str, request: Request):
    return await openai.retrive_model(request, model)


@router.post("/chat/completions")
async def chat_completions(params: OpenAIV1ChatCompletion, request: Request):
    return await openai.v1_chat_completions(params, request)


@router.post("/completions")
async def completions(data, request: Request):
    """Given a prompt, the model will return one or more
    predicted completions, and can also return the probabilities
    of alternative tokens at each position.
    """
    return openai.v1_completions(data, request)


@router.post("/edits")
async def edits(data, request: Request):
    """Given a prompt and an instruction, the model will
    return an edited version of the prompt.
    """
    return openai.v1_edits(data, request)


@router.post("/images/generations")
async def image_generations(data, request: Request):
    """Creates an image given a prompt.
    """
    return openai.v1_image_generations(data, request)


@router.post("/embeddings")
async def embeddings(data, request: Request):
    """Given a prompt, the model will return a vector embedding
    of the prompt.
    """
    return openai.v1_embeddings(data, request)


# @router.post("/audio/transcriptions")
# async def audio_transcriptions(data, request: Request):
#     return openai.v1_audio_transcriptions(data, request)

@router.post("/fine-tunes")
async def fine_tunes(data, request: Request):
    return await openai.v1_fine_tunes(data, request)


@router.get("/fine-tunes")
async def fine_tunes(request: Request):
    return await openai.v1_fine_tunes(None, request)


@router.get("/fine-tunes/{fine_tune_id}")
async def fine_tunes(fine_tune_id, request: Request):
    return await openai.v1_retrieve_fine_tunes(fine_tune_id, request)


@router.get("/chat/completions")
def send_warning():
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={
        "error": {
            "message": "You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY), or as the password field (with blank username) if you're accessing the API from your browser and are prompted for a username and password. You can obtain an API key from https://platform.openai.com/account/api-keys.",
            "type": "invalid_request_error",
            "param": None,
            "code": None
        }
    })
