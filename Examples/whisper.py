from openai import OpenAI
from sparrow import relp, yaml_load

config = yaml_load("config.yaml")

client = OpenAI(
    base_url=config["api_base"],
    api_key=config["api_key"],
)

audio_file = open("/path/to/audio.mp3", "rb")
transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
print(transcript)
