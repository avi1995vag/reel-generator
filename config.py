import os

# --- Content ---
TOPIC = "5 morning habits that boost productivity"
NUM_SCENES = 5                 # how many script beats / video segments
LANGUAGE = os.environ.get("REEL_LANGUAGE", "en-IN")
                                 # e.g. "ta-IN" Tamil, "hi-IN" Hindi, "te-IN" Telugu,
                                 # "kn-IN" Kannada, "ml-IN" Malayalam, "bn-IN" Bengali
TONE = "energetic, punchy, scroll-stopping"   # style hint for the script

# --- Voice ---
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"   # ⚠️ same model generation as the
                                 # gemini-2.5-flash text model that got deprecated --
                                 # if voice_generator.py starts throwing a 404, check
                                 # https://ai.google.dev/gemini-api/docs/speech-generation
                                 # for the current TTS model ID and update this.
VOICE_NAME = "Kore"             # pick from Gemini's prebuilt voice list

# --- Avatar ---
AVATAR_IMAGE = "avatar_engine/my_avatar.jpg"   # a clear, front-facing photo
AVATAR_BACKEND = "hosted"        # "hosted" = free, no GPU needed (calls a public
                                  # Hugging Face Space). "local" = self-hosted
                                  # SadTalker/Wav2Lip, needs your own/Colab GPU.
AVATAR_ENGINE = "sadtalker"      # only used when AVATAR_BACKEND == "local":
                                  # "sadtalker" (photo) or "wav2lip" (existing video)
AVATAR_SOURCE_VIDEO = None       # only needed if AVATAR_ENGINE == "wav2lip"

# --- Output ---
OUTPUT_DIR = "output"
SCENES_DIR = "scenes"
VIDEO_ASPECT = "9:16"            # Reels / Shorts vertical format
FPS = 30
