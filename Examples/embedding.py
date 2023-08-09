import openai
from sparrow import yaml_load

config = yaml_load("config.yaml")
openai.api_base = config["api_base"]
openai.api_key = config["api_key"]
response = openai.Embedding.create(
    input="Your text string goes here", model="text-embedding-ada-002"
)
embeddings = response['data'][0]['embedding']
print(embeddings)
