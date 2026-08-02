# Avatar engine setup

You need ONE of these. Both are free and open source. Clone them as a
sibling folder to `reel-generator/` (not inside it, since they're separate
repos with their own big model checkpoints).

## Option A — SadTalker (recommended if you only have a photo)

```bash
cd ..
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker
pip install -r requirements.txt
bash scripts/download_models.sh    # downloads checkpoints, ~2-3GB
```

Put a clear, front-facing photo of your presenter/avatar at
`reel-generator/avatar_engine/my_avatar.jpg`.

Test it manually first:
```bash
python inference.py \
  --driven_audio ../reel-generator/output/audio/scene_1.wav \
  --source_image ../reel-generator/avatar_engine/my_avatar.jpg \
  --result_dir ../reel-generator/output/avatar_clips \
  --still --preprocess full --enhancer gfpgan
```

No GPU on your machine? Run SadTalker for free on Google Colab — search
"SadTalker Colab notebook" on the project's GitHub README for an
up-to-date link, since hosted notebook links change over time.

## Option B — Wav2Lip (if you already have a video of the presenter)

```bash
cd ..
git clone https://github.com/Rudrabha/Wav2Lip.git
cd Wav2Lip
pip install -r requirements.txt
# download wav2lip_gan.pth checkpoint per the repo's README
```

```bash
python inference.py \
  --checkpoint_path wav2lip_gan.pth \
  --face ../reel-generator/avatar_engine/my_avatar_video.mp4 \
  --audio ../reel-generator/output/audio/scene_1.wav \
  --outfile ../reel-generator/output/avatar_clips/scene_1.mp4
```

## Wiring it into the pipeline

`avatar_generator.py` in the main repo just shells out to whichever tool
you installed — edit the `SADTALKER_DIR` / `WAV2LIP_DIR` paths at the top
of that file to match where you cloned them.
