"""
Step 3: audio/scene_N.wav + avatar photo -> avatar_clips/scene_N.mp4

Two modes, controlled by config.AVATAR_BACKEND:

  "hosted"  (default, fully online, no GPU/install needed) -- calls a
            public SadTalker Space on Hugging Face via gradio_client.
            Runs on HF's free shared GPU queue. Good for getting started
            and for low volume. Can be slow/queued at busy times since
            you're sharing GPU capacity with everyone else using that
            public Space.

  "local"   -- shells out to a SadTalker/Wav2Lip checkout you installed
            yourself (see avatar_engine/README.md). Faster and more
            reliable once set up, but needs a local or Colab GPU.

Resilience: each scene gets up to AVATAR_MAX_RETRIES attempts (the hosted
free queue occasionally times out or errors transiently). If a scene still
fails after retries, it does NOT get silently dropped -- it's recorded in
output/avatar_status.json and printed as a loud warning in the run log, so
you notice it when reviewing the video instead of just seeing a caption
with no avatar bubble and wondering why.

Edit SADTALKER_DIR / WAV2LIP_DIR below only if you use "local" mode.
"""
import glob
import json
import os
import shutil
import subprocess
import time

import config

SADTALKER_DIR = "../SadTalker"
WAV2LIP_DIR = "../Wav2Lip"

# Public Hugging Face Space hosting a SadTalker Gradio demo.
# Check https://huggingface.co/spaces?search=sadtalker for currently-active
# alternatives if this one is down, renamed, or overloaded -- public Spaces
# come and go, so treat this as a starting point, not a permanent address.
HF_SADTALKER_SPACE = "John6666/SadTalker"

AVATAR_MAX_RETRIES = 3
AVATAR_RETRY_BACKOFF_SEC = 15   # doubles each retry: 15s, 30s, 60s...


def run_sadtalker(audio_path: str, result_dir: str):
    cmd = [
        "python", "inference.py",
        "--driven_audio", os.path.abspath(audio_path),
        "--source_image", os.path.abspath(config.AVATAR_IMAGE),
        "--result_dir", os.path.abspath(result_dir),
        "--still",
        "--preprocess", "full",
        "--enhancer", "gfpgan",
    ]
    subprocess.run(cmd, cwd=SADTALKER_DIR, check=True)


def run_wav2lip(audio_path: str, out_path: str):
    cmd = [
        "python", "inference.py",
        "--checkpoint_path", "wav2lip_gan.pth",
        "--face", os.path.abspath(config.AVATAR_SOURCE_VIDEO),
        "--audio", os.path.abspath(audio_path),
        "--outfile", os.path.abspath(out_path),
    ]
    subprocess.run(cmd, cwd=WAV2LIP_DIR, check=True)


def run_hosted_sadtalker(audio_path: str, out_path: str):
    """Calls a public SadTalker Space on Hugging Face -- no local GPU needed.
    pip install gradio_client first (already in requirements.txt).
    """
    from gradio_client import Client, handle_file

    client = Client(HF_SADTALKER_SPACE)
    # NOTE: the exact api_name / parameter order depends on how that Space's
    # app.py is written. Run client.view_api() once to print the real
    # signature and adjust the call below if it differs.
    result = client.predict(
        source_image=handle_file(config.AVATAR_IMAGE),
        driven_audio=handle_file(audio_path),
        preprocess="full",
        still_mode=True,
        use_enhancer=True,
        api_name="/predict",
    )
    # Gradio returns a local temp file path (or dict with a "video" key
    # depending on the Space) -- normalize both cases.
    result_path = result["video"] if isinstance(result, dict) else result
    shutil.copy(result_path, out_path)


def _generate_avatar_clip_once(scene_id: int, audio_path: str, out_path: str, clips_dir: str):
    if getattr(config, "AVATAR_BACKEND", "hosted") == "hosted":
        run_hosted_sadtalker(audio_path, out_path)
        return

    if config.AVATAR_ENGINE == "sadtalker":
        # SadTalker writes a timestamped file inside result_dir; find & rename it.
        scene_result_dir = os.path.join(clips_dir, f"_raw_{scene_id}")
        os.makedirs(scene_result_dir, exist_ok=True)
        run_sadtalker(audio_path, scene_result_dir)
        produced = glob.glob(os.path.join(scene_result_dir, "*.mp4"))
        if not produced:
            raise RuntimeError(f"SadTalker produced no output for scene {scene_id}")
        os.replace(produced[0], out_path)
    elif config.AVATAR_ENGINE == "wav2lip":
        run_wav2lip(audio_path, out_path)
    else:
        raise ValueError(f"Unknown AVATAR_ENGINE: {config.AVATAR_ENGINE}")


def generate_avatar_clip(scene_id: int, audio_path: str) -> str:
    """Returns the clip path on success. Raises the last error after
    exhausting AVATAR_MAX_RETRIES -- caller decides how to handle it."""
    clips_dir = os.path.join(config.OUTPUT_DIR, "avatar_clips")
    os.makedirs(clips_dir, exist_ok=True)
    out_path = os.path.join(clips_dir, f"scene_{scene_id}.mp4")

    backoff = AVATAR_RETRY_BACKOFF_SEC
    last_error = None
    for attempt in range(1, AVATAR_MAX_RETRIES + 1):
        try:
            _generate_avatar_clip_once(scene_id, audio_path, out_path, clips_dir)
            print(f"[avatar_generator] scene {scene_id} -> {out_path} "
                  f"(attempt {attempt}/{AVATAR_MAX_RETRIES})")
            return out_path
        except Exception as e:
            last_error = e
            print(f"[avatar_generator] ⚠️ scene {scene_id} attempt {attempt}/"
                  f"{AVATAR_MAX_RETRIES} failed: {e}")
            if attempt < AVATAR_MAX_RETRIES:
                print(f"[avatar_generator]   retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2

    raise RuntimeError(
        f"Scene {scene_id} avatar generation failed after {AVATAR_MAX_RETRIES} "
        f"attempts. Last error: {last_error}"
    )


def generate_all_avatar_clips(audio_paths: list[str]) -> list[str]:
    """Per-scene resilient: one scene failing after retries does not abort
    the rest. Failures are recorded in output/avatar_status.json and
    printed as a loud, impossible-to-miss summary at the end -- so a failed
    avatar shows up as a clear notice, not a silently missing bubble."""
    clip_paths = []
    failures = []

    for i, audio_path in enumerate(audio_paths, start=1):
        try:
            clip_paths.append(generate_avatar_clip(i, audio_path))
        except Exception as e:
            clip_paths.append(None)
            failures.append({"scene_id": i, "error": str(e)})

    status = {
        "total_scenes": len(audio_paths),
        "succeeded": len(audio_paths) - len(failures),
        "failed": failures,
    }
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(config.OUTPUT_DIR, "avatar_status.json"), "w") as f:
        json.dump(status, f, indent=2)

    if failures:
        print("\n" + "=" * 60)
        print(f"⚠️  AVATAR WARNING: {len(failures)}/{len(audio_paths)} scene(s) "
              f"have NO talking avatar (captions + B-roll only for those).")
        for f_ in failures:
            print(f"   - Scene {f_['scene_id']}: {f_['error']}")
        print("   See output/avatar_status.json. Common cause: the free")
        print("   Hugging Face Space was overloaded/down -- try re-running,")
        print("   or check HF_SADTALKER_SPACE in avatar_generator.py is current.")
        print("=" * 60 + "\n")
    else:
        print(f"[avatar_generator] ✅ all {len(audio_paths)} scenes succeeded.")

    return clip_paths


if __name__ == "__main__":
    import glob as _glob
    audios = sorted(_glob.glob(os.path.join(config.OUTPUT_DIR, "audio", "scene_*.wav")))
    generate_all_avatar_clips(audios)
