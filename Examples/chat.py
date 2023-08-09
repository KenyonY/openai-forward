import openai
from sparrow import yaml_load

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")
openai.api_base = config["api_base"]
openai.api_key = config["api_key"]

stream = False
resp = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        # {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "user", "content": "hi"},
    ],
    stream=stream,
)

if stream:
    for chunk in resp:
        print(chunk)
    print(type(chunk))
else:
    print(resp.choices)
