# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai
from sparrow import relp

openai.api_base = "http://localhost:8000/v1"
# openai.api_base = "https://api.openai-forward.com/v1"
# openai.api_base = "https://vercel.openai-forward.com/v1"
openai.api_key = "sk-******"

audio_file = open(relp("../.github/data/whisper.m4a"), "rb")
transcript = openai.Audio.transcribe("whisper-1", audio_file)
print(transcript)
