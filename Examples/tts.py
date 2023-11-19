from openai import OpenAI
from sparrow import relp, yaml_load

config = yaml_load("config.yaml")

client = OpenAI(
    base_url=config["api_base"],
    api_key=config["api_key"],
)

speech_file_path = relp("./speech.mp3")
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Today is a wonderful day to build something people love!",
)

response.stream_to_file(speech_file_path)
