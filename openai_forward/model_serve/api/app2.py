import torch
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
from transformers import AutoTokenizer, pipeline, TextStreamer, AutoModelForCausalLM

llms = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 可以根據需求選擇自己需要的模型
    checkpoint = "/home/kunyuan/models/openbmb/MiniCPM3-4B"
    model: AutoModelForCausalLM = AutoModelForCausalLM.from_pretrained(
        checkpoint,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        device_map="auto",
        # use_safetensors=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, trust_remote_code=True)

    streamer = TextStreamer(tokenizer, skip_prompt=True)

    # 創建一個用於文本生成的pipeline。
    text_generation_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        use_cache=True,
        device_map="auto",
        max_length=32768,
        do_sample=True,
        top_k=5,
        num_return_sequences=1,
        streamer=streamer,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )

    # 創建一個pipeline實例，用於後續的語言生成。
    llms["myllm"] = text_generation_pipeline
    yield

app = FastAPI(lifespan=lifespan)

def run_llm(question: str) -> AsyncGenerator:
    llm: pipeline = llms["myllm"]
    response_iter = llm.predict(question)
    for response in response_iter:
        print(response)
        yield f"data: {response}\n\n"

@app.get("/chat")
async def root(question: str) -> StreamingResponse:
    return StreamingResponse(run_llm(question), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)