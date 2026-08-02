"""
End-to-end, fully unattended orchestrator: topic -> final reel.

Local run:   python pipeline.py "your topic here"
Automated:   set REEL_TOPIC env var (GitHub Actions does this for you --
             see .github/workflows/generate-reel.yml) and just run:
             python pipeline.py

No manual steps in between -- script, voice, images, avatar, and edit all
run back to back. You only look at the final MP4 at the end.
"""
import json
import os
import sys

from dotenv import load_dotenv

import config
import script_generator
import voice_generator
import image_sourcer
import avatar_generator
import hyperframes_builder


REQUIRED_ENV = ["GEMINI_API_KEY", "PEXELS_API_KEY"]


def main():
    load_dotenv()

    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        sys.exit(f"Missing required environment variable(s): {', '.join(missing)}. "
                  f"See .env.example / repo secrets.")

    topic = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"\n=== 1/5 Script: '{topic or os.environ.get('REEL_TOPIC') or config.TOPIC}' "
          f"({config.LANGUAGE}) ===")
    script = script_generator.generate_script(topic)

    print("\n=== 2/5 Voiceover audio ===")
    audio_paths = voice_generator.generate_all_voices(script)

    print("\n=== 3/5 Auto-sourcing B-roll images (Pexels) ===")
    image_paths = image_sourcer.source_all_images(script)

    print("\n=== 4/5 Avatar clips (hosted, free GPU via Hugging Face) ===")
    clip_paths = avatar_generator.generate_all_avatar_clips(audio_paths)

    print("\n=== 5/5 Building HyperFrames scene ===")
    scene_path = hyperframes_builder.build_scene(script, clip_paths, image_paths)

    print("\n=== Python side done. Rendering final video: ===")
    render_cmd = (
        f"hyperframes render {scene_path} --out {config.OUTPUT_DIR}/final_reel.mp4 "
        f"--fps {config.FPS} --aspect {config.VIDEO_ASPECT}"
    )
    print(f"  {render_cmd}")
    os.system(render_cmd)  # unattended: actually run it, don't just print it

    final_path = os.path.join(config.OUTPUT_DIR, "final_reel.mp4")
    avatar_status_path = os.path.join(config.OUTPUT_DIR, "avatar_status.json")
    avatar_note = ""
    if os.path.exists(avatar_status_path):
        with open(avatar_status_path) as f:
            status = json.load(f)
        if status["failed"]:
            avatar_note = (f" (note: {len(status['failed'])}/{status['total_scenes']} "
                            f"scene(s) missing avatar -- see output/avatar_status.json)")

    if os.path.exists(final_path):
        print(f"\n✅ Done: {final_path}{avatar_note} -- review this.")
    else:
        print("\n⚠️ Render command didn't produce final_reel.mp4 -- check the "
              "HyperFrames CLI output above, flags/package name may have changed.")


if __name__ == "__main__":
    main()
