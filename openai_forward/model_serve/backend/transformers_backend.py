import os
import asyncio
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, pipeline
from threading import Thread
from typing import Literal, Optional, Sequence
from loguru import logger
import concurrent.futures


class AutoModel:
    # pip install git+https://github.com/huggingface/transformers
    # flash-attention-2:  pip install flash-attn --no-build-isolation
    torch.manual_seed(3407)

    def __init__(self,
                 pretrained_model_name_or_path: str,
                 device: Literal["auto", "cpu", "cuda", "mps"] = "cuda",
                 torch_dtype: Literal["auto", "float32", "float16", "bfloat16"] = "bfloat16",
                 attn_implementation: Literal["eager", "sdpa", "flash_attention_2"] = "flash_attention_2",
                 ):
        if torch_dtype == "float32":
            torch_dtype = torch.float32
        elif torch_dtype == "float16":
            torch_dtype = torch.float16
        elif torch_dtype == "bfloat16":
            torch_dtype = torch.bfloat16

        try:
            asyncio.get_event_loop()
        except RuntimeError:
            logger.warning("There is no current event loop, creating a new one.")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path,
            torch_dtype=torch_dtype,
            attn_implementation=attn_implementation,
            device_map=device, trust_remote_code=True)
        self.semaphore = asyncio.Semaphore(int(os.environ.get("MAX_CONCURRENT", "5")))

    async def infer(self, messages: list[dict], **kwargs):
        loop = asyncio.get_running_loop()
        input_args = (messages,
                      kwargs)
        async with self.semaphore:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return await loop.run_in_executor(pool, self._infer, *input_args)

    @torch.inference_mode()
    def _infer(self, messages: list[dict], input_kwargs: Optional[dict] = {}):
        model_kwargs = {}
        model_kwargs["max_new_tokens"] = input_kwargs.get("max_new_tokens", 1024)
        model_kwargs["top_p"] = input_kwargs.get("top_p", 0.7)
        model_kwargs["temperature"] = input_kwargs.get("temperature", 0.7)
        model_kwargs["do_sample"] = input_kwargs.get("do_sample", True)

        inputs_dict = (self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            return_dict=True,
            add_generation_prompt=True,
        ))
        input_ids = inputs_dict['input_ids'].to(self.device)
        generate_kwargs = dict(
            input_ids=input_ids,
            **model_kwargs
        )

        model_outputs = self.model.generate(
            **generate_kwargs
        )

        output_token_ids = [
            model_outputs[i][len(input_ids[i]):] for i in range(len(input_ids))
        ]
        responses = self.tokenizer.batch_decode(output_token_ids, skip_special_tokens=True)[0]
        return responses

    async def stream_infer(self, messages, **kwargs):
        loop = asyncio.get_running_loop()
        async with self.semaphore:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                stream = self._stream_infer(messages, **kwargs)
                while True:
                    try:
                        yield await loop.run_in_executor(pool, stream)
                    except StopAsyncIteration:
                        break

    @torch.inference_mode()
    def _stream_infer(self, messages, **kwargs):
        model_inputs = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True,
        ).to(self.device)
        model_kwargs = {}
        model_kwargs["max_new_tokens"] = kwargs.get("max_new_tokens", 1024)
        model_kwargs["top_p"] = kwargs.get("top_p", 0.7)
        model_kwargs["temperature"] = kwargs.get("temperature", 0.7)
        model_kwargs["do_sample"] = kwargs.get("do_sample", True)
        # model_kwargs["top_k"] = kwargs.get("top_k", 40)
        # model_kwargs['repetition_penalty'] = kwargs.get('repetition_penalty', 1.02)

        streamer = TextIteratorStreamer(self.tokenizer, timeout=100.0, skip_prompt=True, skip_special_tokens=True)
        generate_kwargs = dict(
            input_ids=model_inputs,
            streamer=streamer,
            # eos_token_id=[2, 73440],
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            **model_kwargs,
        )

        Thread(target=self.model.generate, kwargs=generate_kwargs, daemon=True).start()

        def stream():
            try:
                return next(streamer)
            except StopIteration:
                raise StopAsyncIteration()

        return stream
