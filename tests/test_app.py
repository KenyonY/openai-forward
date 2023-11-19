import asyncio

from fastapi.testclient import TestClient
from openai import AsyncOpenAI

from openai_forward.app import app, shutdown, startup

client = TestClient(app)

# stream = False
# async def test_post_chat_completions():
#     await startup()
#     response = client.post("/benchmark/v1/chat/completions",
#                            json=dict(model="gpt-3.5-turbo",
#                                      messages=[{"role": "user", "content": '.'}],
#                                      stream=stream,
#                                      caching=False,
#                                      )
#                            )
#     assert response.status_code == 200
#
#     if stream:
#         for chunk in response.iter_lines():
#             print(chunk)
#     else:
#         print(response.json())
#     await shutdown()

# async def test_openai():
#     client = AsyncOpenAI(
#         api_key="test",
#         base_url="http://localhost:8000/benchmark/v1",
#     )
#     response = await client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "user", "content": '.'},
#         ],
#         stream=stream,
#         timeout=60,
#         extra_body={"caching": False},
#
#     )
#     if stream:
#         async for chunk in response:
#             print(chunk)
#     else:
#         print(response.choices)
#
#
# asyncio.run(test_openai())
