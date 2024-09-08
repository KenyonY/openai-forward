from transformers_stream_generator import init_stream_support
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, pipeline
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import torch
from threading import Thread

# pip install git+https://github.com/huggingface/transformers
# flash-attention-2:  pip install flash-attn --no-build-isolation

torch.manual_seed(0)

device = "cuda"
# path = '/home/kunyuan/models/openbmb/MiniCPM3-4B'
# path = '/home/kunyuan/models/Qwen/Qwen2-7B-Instruct-GPTQ-Int8'
# path = '/home/kunyuan/models/Qwen/Qwen2-VL-2B-Instruct'
path = '/home/kunyuan/models/Qwen/Qwen2-VL-7B-Instruct-AWQ'

# path = '/home/kunyuan/models/Qwen/Qwen2-VL-2B-Instruct'

tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
# model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16, device_map='cuda', trust_remote_code=True)
model = Qwen2VLForConditionalGeneration.from_pretrained(
    path,
    attn_implementation="flash_attention_2",
torch_dtype="auto", device_map='auto')
processor = AutoProcessor.from_pretrained(path )
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "image": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
            },
            {"type": "text", "text": "Describe this image."},
        ],
    }
]
text = processor.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
image_inputs, video_inputs = process_vision_info(messages)
inputs = processor(
    text=[text],
    images=image_inputs,
    videos=video_inputs,
    padding=True,
    return_tensors="pt",
)
inputs = inputs.to("cuda")
# output_ids = model.generate(**inputs, max_new_tokens=128)
# generated_ids = [
#     output_ids[len(input_ids):]
#     for input_ids, output_ids in zip(inputs.input_ids, output_ids)
# ]
# output_text = processor.batch_decode(
#     generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
# )
# print(output_text)
# exit()

model_inputs = inputs
# messages = [
#     {"role": "user", "content": "推荐5个北京的景点。"},
# ]

# model_inputs = tokenizer.apply_chat_template(
#     messages,
#     return_tensors="pt",
#     add_generation_prompt=True,
# ).to(device)

# model_inputs = tokenizer([text], return_tensors="pt").to(device)


# streamer = TextIteratorStreamer(tokenizer, timeout=60.0, skip_prompt=True, skip_special_tokens=True)
streamer = TextIteratorStreamer(processor, timeout=60.0, skip_prompt=True, skip_special_tokens=True)

model_inputs.update(
   dict(
max_new_tokens = 1000,
    do_sample = True,  # False if temperature == 0 else True,
    top_p = 0.7,
    temperature = 0.7,
        # temperature = temperature,
    streamer = streamer,
        # repetition_penalty=penalty,
    # eos_token_id = [2, 73440],
   )
)
generate_kwargs = dict(
    **model_inputs,
)

# generate_kwargs = dict(
#     input_ids=model_inputs,
#     max_new_tokens = 1000, #max_new_tokens,
#     do_sample = True, #False if temperature == 0 else True,
#     top_p=0.7,
#     temperature=0.7,
#     # top_p = top_p,
#     # top_k = top_k,
#     # temperature = temperature,
#     streamer=streamer,
#     # repetition_penalty=penalty,
#     eos_token_id = [2, 73440],
# )
with torch.no_grad():
    thread = Thread(target=model.generate, kwargs=generate_kwargs)
    thread.start()

buffer = ""
for new_text in streamer:
    buffer += new_text
    print(new_text, end="")

