from openai import OpenAI
from sparrow import yaml_load

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")

client = OpenAI(
    api_key=config['api_key'],
    base_url=config['api_base'],
)

my_assistant = client.beta.assistants.create(
    instructions="You are a personal math tutor. When asked a question, write and run Python code to answer the question.",
    name="Math Tutor",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4",
)
print(my_assistant)
