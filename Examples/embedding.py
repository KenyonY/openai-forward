import openai

openai.api_base = "http://localhost:8000/v1"
openai.api_key = "sk-******"
response = openai.Embedding.create(
    input="Your text string goes here", model="text-embedding-ada-002"
)
embeddings = response['data'][0]['embedding']
print(embeddings)
