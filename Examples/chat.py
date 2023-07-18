import openai

openai.api_base = "https://api.openai-forward.com/v1"
openai.api_key = "sk-******"

resp = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Who won the world series in 2020?"},
    ],
)
print(resp.choices)
