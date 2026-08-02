"""
Step: script.json + images/*.jpg + avatar_clips/*.mp4 -> scenes/generated_scene.html

Each scene = auto-sourced stock photo (Ken Burns zoom) as background,
your avatar clip as a small talking picture-in-picture bubble bottom-left,
animated caption text, all timed to match the voiceover duration.

HyperFrames is HTML/CSS as video -- data-* attributes describe clips,
timing, and captions. The framework is actively evolving, so treat this as
a starting point; check https://github.com/HeyGen-Official for the current
syntax if attribute names have changed since this was written.
"""
import json
import os

import config

SCENE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<style>
  :root {{
    --font: 'Poppins', 'Noto Sans', 'Noto Sans Kannada', 'Noto Sans Tamil', sans-serif;
    --accent: #ff5c5c;
    --bg: #0a0a0a;
  }}
  body {{ margin: 0; background: var(--bg); font-family: var(--font); }}
  .scene {{
    position: relative;
    width: 1080px;
    height: 1920px;
    overflow: hidden;
  }}
  .bg {{
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    object-fit: cover;
    animation: kenburns 6s ease-out forwards;
  }}
  @keyframes kenburns {{
    from {{ transform: scale(1.0) translate(0, 0); }}
    to   {{ transform: scale(1.15) translate(-1%, -1%); }}
  }}
  .avatar-pip {{
    position: absolute;
    left: 48px; bottom: 320px;
    width: 320px; height: 320px;
    border-radius: 50%;
    overflow: hidden;
    border: 6px solid white;
    box-shadow: 0 8px 30px rgba(0,0,0,0.5);
  }}
  .avatar-pip video {{ width: 100%; height: 100%; object-fit: cover; }}
  .caption {{
    position: absolute;
    left: 60px; right: 60px; bottom: 700px;
    color: white;
    font-size: 60px;
    font-weight: 700;
    line-height: 1.2;
    text-shadow: 0 4px 20px rgba(0,0,0,0.7);
    animation: rise 0.5s ease-out;
  }}
  @keyframes rise {{
    from {{ transform: translateY(40px); opacity: 0; }}
    to   {{ transform: translateY(0);    opacity: 1; }}
  }}
  .outro {{
    display: flex; align-items: center; justify-content: center;
    width: 1080px; height: 1920px; background: var(--bg);
    color: white; font-size: 56px; font-weight: 700; text-align: center;
  }}
</style>
</head>
<body>

{scenes_html}

<div class="scene outro" data-hf-start="{outro_start}" data-hf-duration="2">
  Follow for more!
</div>

</body>
</html>
"""

SCENE_BLOCK_WITH_AVATAR = """<div class="scene" data-hf-start="{start}" data-hf-duration="{duration}">
  <img class="bg" src="{image_path}" />
  <div class="avatar-pip">
    <video src="{clip_path}" data-hf-audio="track1" autoplay muted></video>
  </div>
  <div class="caption">{caption}</div>
</div>
"""

SCENE_BLOCK_NO_AVATAR = """<div class="scene" data-hf-start="{start}" data-hf-duration="{duration}">
  <img class="bg" src="{image_path}" />
  <audio src="{audio_path}" autoplay></audio>
  <div class="caption">{caption}</div>
</div>
"""


def build_scene(script: dict = None, clip_paths: list[str] = None, image_paths: list[str] = None) -> str:
    if script is None:
        with open(os.path.join(config.OUTPUT_DIR, "script.json"), encoding="utf-8") as f:
            script = json.load(f)

    if clip_paths is None:
        clip_paths = [
            os.path.join(config.OUTPUT_DIR, "avatar_clips", f"scene_{s['id']}.mp4")
            for s in script["scenes"]
        ]
    if image_paths is None:
        image_paths = [
            os.path.join(config.OUTPUT_DIR, "images", f"scene_{s['id']}.jpg")
            for s in script["scenes"]
        ]
    audio_paths = [
        os.path.join(config.OUTPUT_DIR, "audio", f"scene_{s['id']}.wav")
        for s in script["scenes"]
    ]

    blocks = []
    t = 0.0
    for scene, clip_path, image_path, audio_path in zip(
        script["scenes"], clip_paths, image_paths, audio_paths
    ):
        duration = scene.get("duration_hint_sec", 4)
        rel_image = os.path.relpath(image_path, config.SCENES_DIR)
        rel_audio = os.path.relpath(audio_path, config.SCENES_DIR)

        if clip_path:
            blocks.append(
                SCENE_BLOCK_WITH_AVATAR.format(
                    start=round(t, 2),
                    duration=duration,
                    clip_path=os.path.relpath(clip_path, config.SCENES_DIR),
                    image_path=rel_image,
                    caption=scene["on_screen_text"],
                )
            )
        else:
            blocks.append(
                SCENE_BLOCK_NO_AVATAR.format(
                    start=round(t, 2),
                    duration=duration,
                    image_path=rel_image,
                    audio_path=rel_audio,
                    caption=scene["on_screen_text"],
                )
            )
        t += duration

    html = SCENE_TEMPLATE.format(scenes_html="\n".join(blocks), outro_start=round(t, 2))

    os.makedirs(config.SCENES_DIR, exist_ok=True)
    out_path = os.path.join(config.SCENES_DIR, "generated_scene.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[hyperframes_builder] wrote {out_path}")
    return out_path


if __name__ == "__main__":
    build_scene()
