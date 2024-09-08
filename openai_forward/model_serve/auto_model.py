from transformers_stream_generator import init_stream_support
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, pipeline
import torch
from threading import Thread
from typing import Literal



class AutoModel:
    # pip install git+https://github.com/huggingface/transformers
    # flash-attention-2:  pip install flash-attn --no-build-isolation
    torch.manual_seed(3407)

    def __init__(self,
                 pretrained_model_name_or_path: str= '/home/kunyuan/models/openbmb/MiniCPM3-4B',
                 device: Literal["auto", "cpu", "cuda", "mps"]="cuda",
                 torch_dtype: Literal["auto", "float32", "float16", "bfloat16"]="bfloat16",
                 attn_implementation: Literal["eager", "sdpa", "flash_attention_2"] = "flash_attention_2",
                 ):
        # pretrained_model_name_or_path = '/home/kunyuan/models/Qwen/Qwen2-7B-Instruct-GPTQ-Int8'
        if torch_dtype == "float32":
            torch_dtype = torch.float32
        elif torch_dtype == "float16":
            torch_dtype = torch.float16
        elif torch_dtype == "bfloat16":
            torch_dtype = torch.bfloat16

        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path,
            torch_dtype=torch_dtype,
            attn_implementation=attn_implementation,
            device_map=device, trust_remote_code=True)
        self.streamer = TextIteratorStreamer(self.tokenizer, timeout=100.0, skip_prompt=True, skip_special_tokens=True)


    def infer(self, messages, **kwargs):
        model_kwargs = {}
        model_kwargs["max_new_tokens"] = kwargs.get("max_new_tokens", 1024)
        model_kwargs["top_p"] = kwargs.get("top_p", 0.7)
        model_kwargs["temperature"] = kwargs.get("temperature", 0.7)
        model_kwargs["do_sample"] = kwargs.get("do_sample", True)

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

    def stream_infer(self, messages, **kwargs):
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

        generate_kwargs=dict(
            input_ids= model_inputs,
            streamer= self.streamer,
            eos_token_id= [2, 73440],
            **model_kwargs,
        )

        # generate_kwargs = dict(
        #     input_ids=model_inputs,
        #     # top_p = top_p,
        #     # top_k = top_k,
        #     # temperature = temperature,
        #     streamer=streamer,
        #     # repetition_penalty=penalty,
        #     eos_token_id = [2, 73440],
        # )
        with torch.no_grad():
            thread = Thread(target=self.model.generate, kwargs=generate_kwargs)
            thread.start()
        return self.streamer

if __name__ == "__main__":
    messages = [
        {"role": "user", "content": "推荐5个北京的景点。"},
    ]

    model = AutoModel('/home/kunyuan/models/openbmb/MiniCPM3-4B')
    for i in model.stream_infer(messages):
        print(i, end="")

    print(model.infer(messages))




