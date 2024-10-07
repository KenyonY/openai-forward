from vllm import AsyncEngineArgs, AsyncLLMEngine, RequestOutput, SamplingParams, LLM
from vllm.lora.request import LoRARequest
from transformers import AutoTokenizer, GenerationConfig
from typing import Literal
from .misc import get_device_count
import uuid



class VllmEngine:

    # vllm engine args: https://docs.vllm.ai/en/latest/models/engine_args.html

    def __init__(self,
                 pretrained_model_name_or_path: str,
                 device='auto',
                 quantization=None,
                 max_model_len=16000,
                 infer_dtype="bfloat16",
                 enforce_eager=False,
                 enable_prefix_caching=False,
                 max_num_seqs=3,
                 seed=3407,
                 ):
        print(f"{max_model_len=}")
        print(f"{quantization=}")
        if quantization == 'gptq':
            infer_dtype = "float16"

        engine_args = {
            "model": pretrained_model_name_or_path,
            "seed": seed,
            "trust_remote_code": True,
            # "download_dir": model_args.cache_dir,
            "dtype": infer_dtype,
            "max_model_len": max_model_len,
            "tensor_parallel_size": get_device_count() or 1,
            # "gpu_memory_utilization": model_args.vllm_gpu_util,
            "device": device,
            "disable_log_stats": True,
            "disable_log_requests": True,

            "enforce_eager": enforce_eager,
            # "enable_lora": model_args.adapter_name_or_path is not None,
            # "max_lora_rank": model_args.vllm_max_lora_rank,

            "enable_prefix_caching": enable_prefix_caching,
            "max_num_seqs": max_num_seqs,
            "quantization": quantization,
        }
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path,
                                                       trust_remote_code=True)
        self.tokenizer.padding_side = "left"
        self.model = AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**engine_args))
        self.generation_config = GenerationConfig.from_pretrained(pretrained_model_name_or_path)
        self.generation_config.pad_token_id = self.tokenizer.pad_token_id

    def _generate(self, messages: list[dict], **kwargs):
        sampling_params = SamplingParams(
            n=1,
            repetition_penalty=1.0,  # repetition_penalty must > 0
            temperature=1.0,  # if temperature is not None else self.generating_args["temperature"],
            top_p=1.0,  # top_p must > 0
            # top_k=,
            # use_beam_search=use_beam_search,
            # length_penalty=length_penalty if length_penalty is not None else self.generating_args["length_penalty"],
            # stop=stop,
            stop_token_ids=[self.tokenizer.eos_token_id] + self.tokenizer.additional_special_tokens_ids,
            max_tokens=kwargs.get("max_tokens", 4096),
            skip_special_tokens=True,
        )
        request_id = "chatcmpl-{}".format(uuid.uuid4().hex)
        # paired_messages = messages + [{"role": "assistant", "content": ""}]
        # system = None
        result_generator = self.model.generate(
            inputs=messages[0]["content"], # todo: fixme
            sampling_params=sampling_params,
            request_id=request_id,
            # lora_request=self.lora_request,
        )
        return result_generator

    async def stream_infer(self, messages, **kwargs):
        generated_text = ""
        generator = self._generate(messages, **kwargs)
        async for result in generator:
            delta_text = result.outputs[0].text[len(generated_text):]
            generated_text = result.outputs[0].text
            print(delta_text)
            yield delta_text

    async def infer(self, messages: list[dict], **kwargs):
        generator = self._generate(messages, **kwargs)
        async for request_output in generator:
            return [outputs.text for outputs in request_output.outputs][0]


