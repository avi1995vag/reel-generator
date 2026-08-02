"""
Step 2: script.json -> one WAV file per scene using Gemini native TTS.

NOTE on languages: Gemini's native TTS preview models auto-detect the
input text's language and pick a matching voice. Language coverage is
still growing (Preview) -- Hindi and several major Indian languages are
supported; if your target language (e.g. Tamil) isn't producing good
results, swap this module's client calls for Google Cloud Text-to-Speech
(https://cloud.google.com/text-to-speech) instead, which has 75+ languages
including Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi with native
voices. The rest of this pipeline (avatar + HyperFrames) doesn't care which
TTS backend produced the audio.
"""
import base64
import mimetypes
import os
import struct
import wave

from google import genai
from google.genai import types

import config


def _save_pcm_as_wav(pcm_data: bytes, path: str, channels=1, rate=24000, sample_width=2):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def generate_voice_for_scene(client, text: str, out_path: str):
    response = client.models.generate_content(
        model=config.GEMINI_TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=config.VOICE_NAME
                    )
                )
            ),
        ),
    )

    part = response.candidates[0].content.parts[0]
    audio_bytes = part.inline_data.data
    # Gemini TTS returns raw PCM (16-bit, 24kHz, mono) -- wrap it in a WAV header.
    _save_pcm_as_wav(audio_bytes, out_path)


def generate_all_voices(script: dict = None):
    import json

    if script is None:
        with open(os.path.join(config.OUTPUT_DIR, "script.json"), encoding="utf-8") as f:
            script = json.load(f)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    audio_dir = os.path.join(config.OUTPUT_DIR, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    paths = []
    for scene in script["scenes"]:
        out_path = os.path.join(audio_dir, f"scene_{scene['id']}.wav")
        generate_voice_for_scene(client, scene["voiceover"], out_path)
        print(f"[voice_generator] scene {scene['id']} -> {out_path}")
        paths.append(out_path)

    return paths


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    generate_all_voices()
