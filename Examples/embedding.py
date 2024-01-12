from openai import OpenAI
from sparrow import yaml_load

config = yaml_load("config.yaml")
client = OpenAI(
    api_key=config['api_key'],
    base_url=config['api_base'],
)

response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="你好",
    encoding_format="float",
    # encoding_format="base64",
    extra_body={"caching": True},
)

print(response)
