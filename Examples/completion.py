import openai
from rich import print
from rich.console import Console
from rich.markdown import Markdown
from sparrow import yaml_load  # pip install sparrow-python

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")
openai.api_base = config["api_base"]
openai.api_key = config["api_key"]


stream = True
# debug=True
debug = False


user_content = "现在让我们使用泰勒展开推导出牛顿法迭代公式:  \n"

resp = openai.Completion.create(
    model="gpt-3.5-turbo-instruct",
    prompt=user_content,
    stream=stream,
    max_tokens=500,
    request_timeout=30,
)

console = Console()
sentences = ""
if stream:
    if debug:
        for chunk in resp:
            print(chunk)
    else:
        for chunk in resp:
            text = chunk['choices'][0]['text']
            console.print(text, end="")
            sentences += text
    print()
else:
    if debug:
        print(resp)
    else:
        sentences = resp['choices'][0]['text']
        print(sentences)

print(70 * "-")
# console.print(Markdown(sentences))
