import asyncio

from openai import AsyncOpenAI, OpenAI
from rich import print
from sparrow import MeasureTime, yaml_load  # pip install sparrow-python

config = yaml_load("config.yaml", rel_path=True)
print(f"{config=}")

client = AsyncOpenAI(
    api_key=config['api_key'],
    base_url=config['api_base'],
)

stream = True
# stream = False

is_print = False


async def run(n):
    resp = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": '.'},
        ],
        stream=stream,
        timeout=60,
    )

    if stream:
        first_chunk = await anext(resp)
        if first_chunk is not None:
            if is_print:
                chunk_message = first_chunk.choices[0].delta
                print(f"{chunk_message['role']}: ")
            async for chunk in resp:
                if is_print:
                    chunk_message = chunk.choices[0].delta
                    content = chunk_message.content
                    print(content, end="")
            if is_print:
                print()
    else:
        if is_print:
            assistant_content = resp.choices[0].message.content
            print(assistant_content)
            print(resp.usage)

    print(f"Task {n} completed")


async def main():
    mt = MeasureTime().start()
    mean = 0
    epochs = 5
    concurrency = 100
    for epoch in range(epochs):
        tasks = []
        for i in range(concurrency):  # 创建 concurrency 个并发任务
            task = asyncio.create_task(run(i))
            tasks.append(task)

        mt.start()
        await asyncio.gather(*tasks)
        cost = mt.show_interval(f"{epoch=}")
        mean += cost
    mean_cost = mean / epochs
    print(f"mean: {mean_cost} s")
    print(f"{concurrency/mean_cost}req/s")


asyncio.run(main())
