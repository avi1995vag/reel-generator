import os

# --- Content ---
TOPIC = "5 morning habits that boost productivity"
NUM_SCENES = 5                 # how many script beats / video segments
LANGUAGE = os.environ.get("REEL_LANGUAGE", "en-IN")
                                 # e.g. "ta-IN" Tamil, "hi-IN" Hindi, "te-IN" Telugu,
                                 # "kn-IN" Kannada, "ml-IN" Malayalam, "bn-IN" Bengali
TONE = "energetic, punchy, scroll-stopping"   # style hint for the script

# --- Voice ---
TTS_BACKEND = "edge"            # "edge" = free, no API key, no billing (recommended).
                                 # "gemini" = Gemini native TTS -- needs GEMINI_API_KEY,
                                 # has a small free-tier daily request cap.
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"   # ⚠️ same model generation as the
                                 # gemini-2.5-flash text model that got deprecated --
                                 # if voice_generator.py starts throwing a 404, check
                                 # https://ai.google.dev/gemini-api/docs/speech-generation
                                 # for the current TTS model ID and update this.
VOICE_NAME = "Kore"             # pick from Gemini's prebuilt voice list

# --- Avatar ---
# Defaults to OFF. The "hosted" free option (public Hugging Face Space)
# proved unreliable across testing -- wrong API endpoint name at first,
# then a run that hung for the full 30-minute job timeout without
# finishing. Rather than keep guessing at a third-party demo's internals,
# the pipeline now ships reliably WITHOUT a talking avatar by default:
# captions + auto-sourced B-roll images + voiceover, which has consistently
# worked end to end. Turn avatar back on only once you've verified it
# actually works for your case -- see avatar_engine/README.md for both
# options and their real trade-offs.
AVATAR_IMAGE = "avatar_engine/my_avatar.jpg"   # a clear, front-facing photo
AVATAR_BACKEND = "none"          # "none" = skip avatar, captions+B-roll only (reliable).
                                  # "hosted" = free public Hugging Face Space -- flaky,
                                  # see the warning above.
                                  # "local" = self-hosted SadTalker/Wav2Lip, needs your
                                  # own/Colab GPU -- most reliable if you want a real avatar.
AVATAR_ENGINE = "sadtalker"      # only used when AVATAR_BACKEND == "local":
                                  # "sadtalker" (photo) or "wav2lip" (existing video)
AVATAR_SOURCE_VIDEO = None       # only needed if AVATAR_ENGINE == "wav2lip"
AVATAR_REQUEST_TIMEOUT_SEC = 90   # hard cap per hosted API call so a stuck
                                  # request can't hang the whole job again

# --- Output ---
OUTPUT_DIR = "output"
SCENES_DIR = "scenes"
VIDEO_ASPECT = "9:16"            # Reels / Shorts vertical format
FPS = 30
