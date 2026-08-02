"""
Step 2: script.json -> one audio file per scene.

Default backend: edge-tts -- genuinely free, no API key, no billing, no
card required. It's an unofficial wrapper around the neural voices behind
Microsoft Edge's browser read-aloud feature, but it's widely used and
stable. This replaces the earlier Gemini-native-TTS default, which hit two
walls in testing: a tiny per-minute rate limit, then a hard 10-requests/day
cap on the free tier that pacing/retries can't work around. Google Cloud
TTS (the other alternative) has a generous free character allowance but
requires enabling billing on the GCP project even to use it, so it's not
a true no-card option.

Voice selection is dynamic: rather than hardcoding an exact voice name
(which risks being wrong/renamed), this looks up available voices by
locale (e.g. "kn-IN") at request time via edge_tts.VoicesManager and picks
a matching one automatically.

Fallback: set config.TTS_BACKEND = "gemini" to use Gemini's native TTS
instead (useful if you've enabled billing on your Gemini API project and
want higher request limits).
"""
import asyncio
import os
import time
import wave

import config


# ---------------------------------------------------------------------------
# Backend 1: edge-tts (default, free, no key)
# ---------------------------------------------------------------------------

async def _edge_tts_synthesize(text: str, locale: str, out_path: str):
    import edge_tts

    voices = await edge_tts.list_voices()
    manager = await edge_tts.VoicesManager.create(voices)
    matches = manager.find(Locale=locale)
    if not matches:
        raise RuntimeError(
            f"No edge-tts voice found for locale '{locale}'. Run "
            f"`edge-tts --list-voices` to see available locales and adjust "
            f"config.LANGUAGE to match one exactly (e.g. 'kn-IN', 'hi-IN')."
        )
    voice_name = matches[0]["Name"]
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(out_path)
    return voice_name


def generate_voice_for_scene_edge(text: str, out_path: str) -> str:
    """out_path should end in .mp3 -- edge-tts outputs mp3 natively."""
    return asyncio.run(_edge_tts_synthesize(text, config.LANGUAGE, out_path))


# ---------------------------------------------------------------------------
# Backend 2: Gemini native TTS (fallback, needs GEMINI_API_KEY + quota)
# ---------------------------------------------------------------------------

def _save_pcm_as_wav(pcm_data: bytes, path: str, channels=1, rate=24000, sample_width=2):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def generate_voice_for_scene_gemini(client, text: str, out_path: str):
    from google.genai import types

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
    _save_pcm_as_wav(part.inline_data.data, out_path)


def generate_voice_for_scene_gemini_with_retry(client, text: str, out_path: str, scene_id: int):
    from google.genai.errors import ClientError

    backoff = 30
    for attempt in range(1, 5):
        try:
            generate_voice_for_scene_gemini(client, text, out_path)
            return
        except ClientError as e:
            is_quota = getattr(e, "status_code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e)
            if not is_quota or attempt == 4:
                raise
            print(f"[voice_generator] scene {scene_id}: quota hit (attempt {attempt}/4), "
                  f"waiting {backoff}s...")
            time.sleep(backoff)
            backoff *= 2


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def generate_all_voices(script: dict = None):
    import json

    if script is None:
        with open(os.path.join(config.OUTPUT_DIR, "script.json"), encoding="utf-8") as f:
            script = json.load(f)

    audio_dir = os.path.join(config.OUTPUT_DIR, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    backend = getattr(config, "TTS_BACKEND", "edge")
    gemini_client = None
    if backend == "gemini":
        from google import genai
        gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    paths = []
    for i, scene in enumerate(script["scenes"]):
        ext = "mp3" if backend == "edge" else "wav"
        out_path = os.path.join(audio_dir, f"scene_{scene['id']}.{ext}")

        if backend == "edge":
            voice_used = generate_voice_for_scene_edge(scene["voiceover"], out_path)
            print(f"[voice_generator] scene {scene['id']} -> {out_path} (voice: {voice_used})")
        else:
            if i > 0:
                time.sleep(21)   # stay under Gemini free-tier per-minute limit
            generate_voice_for_scene_gemini_with_retry(
                gemini_client, scene["voiceover"], out_path, scene["id"]
            )
            print(f"[voice_generator] scene {scene['id']} -> {out_path}")

        paths.append(out_path)

    return paths


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    generate_all_voices()
