from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

# 目前minicpm3-4b还没有被vllm官方支持，所以最好时再等等,别浪费时间按照minicpm fork的vllm了.
model_name = "/home/kunyuan/models/openbmb/MiniCPM3-4B"
prompt = [{"role": "user", "content": "推荐5个北京的景点。"}]

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
device = "auto"
input_text = tokenizer.apply_chat_template(
    prompt, tokenize=False, add_generation_prompt=True)
print(input_text)

llm = LLM(
    model=model_name,
    trust_remote_code=True,
    tensor_parallel_size=1
)
sampling_params = SamplingParams(top_p=0.7, temperature=0.7, max_tokens=1024, repetition_penalty=1.02)

outputs = llm.generate(prompts=input_text, sampling_params=sampling_params)

print(outputs[0].outputs[0].text)
