import time

import openai
from rich import print
from sparrow import yaml_load

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")
openai.api_base = config["api_base"]
openai.api_key = config["api_key"]

stream = True
user_content = """
用c实现快速平方根算法
"""

resp = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": user_content},
    ],
    stream=stream,
)

if stream:
    chunk_message = next(resp)['choices'][0]['delta']
    print(f"{chunk_message['role']}: ")
    for chunk in resp:
        chunk_message = chunk['choices'][0]['delta']
        content = chunk_message.get("content", "")
        print(content, end="")
    print()
else:
    print(resp.choices)
