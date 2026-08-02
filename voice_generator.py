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

NOTE on rate limits: the free tier for this TTS model allows only a
handful of requests per minute (Google's error message reports the exact
number when you hit it, e.g. "limit: 3"). This module paces requests with
a fixed delay between scenes and retries with backoff if a 429
RESOURCE_EXHAUSTED error slips through anyway, so a 5+ scene video doesn't
just fail outright on the free tier.
"""
import os
import time
import wave

from google import genai
from google.genai import types
from google.genai.errors import ClientError

import config

# Free tier is tight (observed as low as 3 requests/minute for this model).
# Space calls out so we don't even try to burst past that.
SECONDS_BETWEEN_REQUESTS = 21   # ~3 req/min pace, safely under the ceiling
MAX_RETRIES = 4
RETRY_BACKOFF_SEC = 30           # doubles each retry: 30s, 60s, 120s...


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


def generate_voice_for_scene_with_retry(client, text: str, out_path: str, scene_id: int):
    backoff = RETRY_BACKOFF_SEC
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            generate_voice_for_scene(client, text, out_path)
            return
        except ClientError as e:
            is_quota = getattr(e, "status_code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e)
            if not is_quota or attempt == MAX_RETRIES:
                raise
            print(f"[voice_generator] scene {scene_id}: quota hit (attempt "
                  f"{attempt}/{MAX_RETRIES}), waiting {backoff}s before retry...")
            time.sleep(backoff)
            backoff *= 2


def generate_all_voices(script: dict = None):
    import json

    if script is None:
        with open(os.path.join(config.OUTPUT_DIR, "script.json"), encoding="utf-8") as f:
            script = json.load(f)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    audio_dir = os.path.join(config.OUTPUT_DIR, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    paths = []
    for i, scene in enumerate(script["scenes"]):
        if i > 0:
            time.sleep(SECONDS_BETWEEN_REQUESTS)   # stay under free-tier rate limit

        out_path = os.path.join(audio_dir, f"scene_{scene['id']}.wav")
        generate_voice_for_scene_with_retry(client, scene["voiceover"], out_path, scene["id"])
        print(f"[voice_generator] scene {scene['id']} -> {out_path}")
        paths.append(out_path)

    return paths


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    generate_all_voices()
