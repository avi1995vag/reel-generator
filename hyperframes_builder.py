"""
Step: script.json + images/*.jpg + avatar_clips/*.mp4 -> scenes/generated_scene.html

Builds one HyperFrames composition: a single "stage" containing all clips,
each with its own data-start / data-duration / data-track-index. Tracks
stack for compositing (higher index draws on top); clips on the same
track play sequentially at their own start time.

  track 0: background stock photo per scene (Ken Burns zoom)
  track 1: avatar video PiP bubble per scene (when available)
  track 2: caption text per scene
  track 3: voiceover audio per scene (always present, independent of
           whether the avatar video rendered, so audio never goes missing)

Real HyperFrames syntax reference: https://github.com/heygen-com/hyperframes
Run `npx hyperframes lint <file>` locally if a render fails -- it flags
composition issues (overlapping clips, bad attributes) directly.
"""
import json
import os

import config

STAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<style>
  :root {{
    --font: 'Poppins', 'Noto Sans', 'Noto Sans Kannada', 'Noto Sans Tamil', sans-serif;
    --bg: #0a0a0a;
  }}
  body {{ margin: 0; background: var(--bg); font-family: var(--font); }}
  #stage {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--bg); }}
  .clip {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
  .bg {{ object-fit: cover; }}
  .avatar-pip {{
    position: absolute; left: 48px; bottom: 320px;
    width: 320px; height: 320px; border-radius: 50%; overflow: hidden;
    border: 6px solid white; box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    inset: auto;
  }}
  .avatar-pip video {{ width: 100%; height: 100%; object-fit: cover; }}
  .caption {{
    position: absolute; left: 60px; right: 60px; bottom: 700px;
    color: white; font-size: 60px; font-weight: 700; line-height: 1.2;
    text-shadow: 0 4px 20px rgba(0,0,0,0.7);
    width: auto; height: auto; inset: auto;
  }}
  .outro {{
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 56px; font-weight: 700; text-align: center;
  }}
</style>
</head>
<body>

<div id="stage" data-composition-id="generated_reel" data-start="0" data-width="1080" data-height="1920">
{clips_html}
  <div class="clip outro" data-start="{outro_start}" data-duration="2" data-track-index="4">
    Follow for more!
  </div>
</div>

</body>
</html>
"""

BG_CLIP = """  <img class="clip bg" src="{image_path}" data-start="{start}" data-duration="{duration}" data-track-index="0" />"""

AVATAR_CLIP = """  <div class="avatar-pip" data-start="{start}" data-duration="{duration}" data-track-index="1">
    <video src="{clip_path}" muted playsinline></video>
  </div>"""

CAPTION_CLIP = """  <div class="clip caption" data-start="{start}" data-duration="{duration}" data-track-index="2">{caption}</div>"""

AUDIO_CLIP = """  <audio src="{audio_path}" data-start="{start}" data-duration="{duration}" data-track-index="3"></audio>"""


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

    clip_blocks = []
    t = 0.0
    for scene, clip_path, image_path, audio_path in zip(
        script["scenes"], clip_paths, image_paths, audio_paths
    ):
        duration = scene.get("duration_hint_sec", 4)
        start = round(t, 2)

        clip_blocks.append(BG_CLIP.format(
            image_path=os.path.relpath(image_path, config.SCENES_DIR),
            start=start, duration=duration,
        ))

        if clip_path:
            clip_blocks.append(AVATAR_CLIP.format(
                clip_path=os.path.relpath(clip_path, config.SCENES_DIR),
                start=start, duration=duration,
            ))

        clip_blocks.append(CAPTION_CLIP.format(
            caption=scene["on_screen_text"], start=start, duration=duration,
        ))

        clip_blocks.append(AUDIO_CLIP.format(
            audio_path=os.path.relpath(audio_path, config.SCENES_DIR),
            start=start, duration=duration,
        ))

        t += duration

    html = STAGE_TEMPLATE.format(
        clips_html="\n".join(clip_blocks),
        outro_start=round(t, 2),
    )

    os.makedirs(config.SCENES_DIR, exist_ok=True)
    out_path = os.path.join(config.SCENES_DIR, "generated_scene.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[hyperframes_builder] wrote {out_path}")
    return out_path


if __name__ == "__main__":
    build_scene()
