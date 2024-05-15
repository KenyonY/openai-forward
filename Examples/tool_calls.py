from openai import OpenAI
from rich import print
from sparrow import MeasureTime, yaml_load  # pip install sparrow-python

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")

client = OpenAI(
    api_key=config['api_key'],
    base_url=config['api_base'],
)
stream = True

n = 1

# debug = True
debug = False

caching = True

max_tokens = None

model = "gpt-3.5-turbo"
# model="gpt-4"

mt = MeasureTime().start()
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
resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "What's the weather like in Boston today?"}],
    tools=tools,
    tool_choice="auto",  # auto is default, but we'll be explicit
    stream=stream,
    extra_body={"caching": caching},
)

if stream:
    if debug:
        for chunk in resp:
            print(chunk)
    else:
        for idx, chunk in enumerate(resp):
            chunk_message = chunk.choices[0].delta or ""
            if idx == 0:
                mt.show_interval("tcp time:")
                function = chunk_message.tool_calls[0].function
                name = function.name
                print(f"{chunk_message.role}: \n{name}: ")
                continue

            content = ""
            tool_calls = chunk_message.tool_calls
            if tool_calls:
                function = tool_calls[0].function
                if function:
                    content = function.arguments or ""
            print(content, end="")
        print()
else:
    print(resp)
    assistant_content = resp.choices[0].message.content
    print(assistant_content)
    print(resp.usage)

mt.show_interval("tool_calls")
