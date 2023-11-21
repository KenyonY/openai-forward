from openai import OpenAI
from openai._types import Headers, Query
from rich import print
from sparrow import MeasureTime, yaml_load  # pip install sparrow-python

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")

client = OpenAI(
    api_key=config['api_key'],
    base_url=config['api_base'],
)

# extra_body={"caching": True}
extra_body = {}
stream = True

json_obj_case = True
function_case = True

if json_obj_case:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON.",
            },
            {"role": "user", "content": "Who won the world series in 2020?"},
        ],
        stream=stream,
        extra_body=extra_body,
    )
    if stream:
        for chunk in response:
            print(chunk)
    else:
        print(response.choices[0].message.content)

if function_case:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]
    messages = [{"role": "user", "content": "What's the weather like in Boston today?"}]
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=stream,
        extra_body=extra_body,
    )

    if stream:
        for chunk in completion:
            print(chunk)
    else:
        print(completion)
