# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai
from sparrow import relp, yaml_load

config = yaml_load("config.yaml")
openai.api_base = config["api_base"]
openai.api_key = config["api_key"]
audio_file = open(relp("../.github/data/whisper.m4a"), "rb")
transcript = openai.Audio.transcribe("whisper-1", audio_file)
print(transcript)
