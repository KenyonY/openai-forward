import os
import requests
from rich import print


def test_api():
    # base_url = 'https://api.openai.com'
    base_url = "http://localhost:8000"
    req_url = f'{base_url}/v1/chat/completions'
    print(req_url)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-xxx",
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": True
    }
    response = requests.post(req_url, stream=True, headers=headers, json=payload)
    assert response.status_code == 200
    for chunk in response.iter_content(chunk_size=128):
        if chunk:
            print(chunk.decode("utf-8"))


if __name__ == '__main__':
    test_api()
