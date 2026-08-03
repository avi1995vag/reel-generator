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
import subprocess
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

    print("\n=== 4/5 Avatar clips ===")
    clip_paths = avatar_generator.generate_all_avatar_clips(audio_paths)

    print("\n=== 5/5 Building HyperFrames scene ===")
    scene_path = hyperframes_builder.build_scene(script, clip_paths, image_paths)

    print("\n=== Python side done. Rendering final video: ===")
    final_path = os.path.join(config.OUTPUT_DIR, "final_reel.mp4")
    render_cmd = ["npx", "--yes", "hyperframes", "render", "-c", scene_path, "-o", final_path]
    print(f"  {' '.join(render_cmd)}")

    # Use subprocess (not os.system) so we capture the real exit code and
    # full output -- a prior version used os.system() and only inferred
    # failure from the file not existing, which meant a broken render
    # still showed a green checkmark in GitHub Actions.
    render_result = subprocess.run(render_cmd, capture_output=True, text=True)
    print(render_result.stdout)
    if render_result.stderr:
        print(render_result.stderr, file=sys.stderr)

    avatar_status_path = os.path.join(config.OUTPUT_DIR, "avatar_status.json")
    avatar_note = ""
    if os.path.exists(avatar_status_path):
        with open(avatar_status_path) as f:
            status = json.load(f)
        if status.get("failed"):
            avatar_note = (f" (note: {len(status['failed'])}/{status['total_scenes']} "
                            f"scene(s) missing avatar -- see output/avatar_status.json)")

    if render_result.returncode == 0 and os.path.exists(final_path):
        print(f"\n✅ Done: {final_path}{avatar_note} -- review this.")
    else:
        print(f"\n❌ Render failed (exit code {render_result.returncode}) -- "
              f"final_reel.mp4 was not produced. See the render output above "
              f"for the actual error. Common causes: HyperFrames CLI version/flag "
              f"changes, missing ffmpeg, or a composition HTML issue -- try "
              f"`npx hyperframes lint {scene_path}` locally to check the composition, "
              f"and `npx hyperframes doctor` to check the environment.")
        sys.exit(1)   # non-zero exit -> GitHub Actions job shows a real failure,
                       # not a misleading green checkmark with no video attached


if __name__ == "__main__":
    main()
