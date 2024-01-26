import requests
from rich import print
from sparrow import yaml_load  # pip install sparrow-python

from openai_forward.helper import urljoin

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")


route = "/v1/models/gemini-pro:generateContent"
url = urljoin(config['api_base'], route)

# url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
print(url)

api_key = config['api_key']

data = {"contents": [{"parts": [{"text": "hi!"}]}]}

response = requests.post(url, json=data, params={"key": api_key})

print(response.json())
