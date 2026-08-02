"""
Step 1: Topic -> scene-by-scene script (JSON) using Gemini.

Produces output/script.json shaped like:
{
  "title": "...",
  "scenes": [
    {"id": 1, "voiceover": "...", "on_screen_text": "...", "duration_hint_sec": 4},
    ...
  ]
}
"""
import json
import os
from google import genai
from google.genai import types

import config


SYSTEM_PROMPT = """You are a short-form video scriptwriter for Instagram
Reels / YouTube Shorts. Write tight, scroll-stopping scripts. Every scene's
voiceover should be speakable in 3-6 seconds. Respond with ONLY valid JSON,
no markdown fences, no commentary, matching exactly this schema:

{{
  "title": "string",
  "scenes": [
    {{
      "id": 1,
      "voiceover": "string in {language_name}, natural spoken style",
      "on_screen_text": "short caption/hook text, <=8 words, in {language_name}",
      "image_query": "2-4 word ENGLISH keyword phrase for stock photo search that visually matches this scene, e.g. 'sunrise yoga mat' or 'person writing journal'",
      "duration_hint_sec": 4
    }}
  ]
}}

Write exactly {num_scenes} scenes. Tone: {tone}. Keep image_query in English
regardless of the target language, since it's used for stock photo search.
"""

LANGUAGE_NAMES = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "bn-IN": "Bengali",
    "mr-IN": "Marathi",
}


def generate_script(topic: str = None) -> dict:
    topic = topic or os.environ.get("REEL_TOPIC") or config.TOPIC
    language_name = LANGUAGE_NAMES.get(config.LANGUAGE, config.LANGUAGE)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    system_prompt = SYSTEM_PROMPT.format(
        language_name=language_name,
        num_scenes=config.NUM_SCENES,
        tone=config.TONE,
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Topic: {topic}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.9,
        ),
    )

    script = json.loads(response.text)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(config.OUTPUT_DIR, "script.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"[script_generator] wrote {out_path} ({len(script['scenes'])} scenes)")
    return script


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    generate_script()
