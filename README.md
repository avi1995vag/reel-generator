# Auto Reel Generator — fully automatic

You do two things: type a topic, and watch/review the finished video.
Everything else — script, voice, images, editing, rendering — runs
unattended.

```
Topic (you type this)
  → Gemini writes the script (auto)
  → edge-tts voices it in your language, free, no API key (auto)
  → Pexels sources matching stock images per scene (auto)
  → HyperFrames composites everything + captions (auto)
  → final_reel.mp4 (you review this)
```

**Note on the avatar (talking-head) feature:** it exists in this repo but
is OFF by default. In testing, the free "hosted" option (a public
Hugging Face Space running SadTalker) proved unreliable — its real API
signature isn't reliably guessable from outside, and calls could hang
well past any reasonable wait. Rather than ship something that
occasionally stalls a whole run, the default pipeline produces reels with
captions + auto-sourced B-roll + voiceover, which has worked consistently
end to end. Want a talking avatar too? See **"Turning the avatar back
on"** below — `Run_On_Colab.ipynb` runs real SadTalker on a free GPU
using your own photo (a manual notebook run, but it actually works,
unlike the earlier hosted attempt).

## One-time setup (5 minutes, never repeat this)

You need two free API keys and one GitHub repo. None of this repeats
per-video — set it up once, then every future video is just "type topic,
click run."

1. **Gemini API key** (free): https://aistudio.google.com/apikey
2. **Pexels API key** (free, for auto-sourced images): https://www.pexels.com/api/
3. **Push this folder to a GitHub repo** (public or private, both work with
   GitHub Actions free tier — public repos get unlimited free minutes,
   private repos get 2,000 free minutes/month, plenty for this).
4. In your repo: **Settings → Secrets and variables → Actions → New
   repository secret**, add:
   - `GEMINI_API_KEY`
   - `PEXELS_API_KEY`

That's the entire setup. You will never touch a terminal, install Python,
or run a notebook cell again after this.

## Making a video, every time after setup

1. Go to your repo on GitHub → **Actions** tab → **Generate Reel** (in the
   left sidebar) → **Run workflow** button.
2. A small form appears: type your **topic** and pick a **language** code
   (`kn-IN` Kannada, `hi-IN` Hindi, `ta-IN` Tamil, `te-IN` Telugu, etc.).
3. Click **Run workflow**. Walk away — should take a few minutes.
4. When it finishes (green checkmark), open that run → scroll to
   **Artifacts** → download `final-reel` → that's your `final_reel.mp4`.
5. Watch it. If the images/voice/pacing aren't right, just run it again
   (each run is a fresh Gemini script + fresh Pexels images, so re-running
   the same topic often gives you a different take to choose from).

No local install, no manual image picking, no manual editing.

## Why this is genuinely hands-off

| Step | How it's automated |
|---|---|
| Script | Gemini writes it from just the topic — no editing needed |
| Images | Gemini also writes a search phrase per scene; Pexels auto-fetches a matching photo, no browsing/picking |
| Voice | edge-tts generates directly from the script text — free, no key, no billing |
| Editing | HyperFrames template auto-places captions, Ken Burns zoom, and timing — no manual scene assembly |
| Trigger | GitHub Actions "Run workflow" button with one text field — no notebook, no CLI |

## Local files (for reference / customizing behavior)

```
config.py               # defaults for topic/language/tone/avatar toggle
script_generator.py     # Gemini: topic -> script + per-scene image queries
voice_generator.py      # edge-tts (default) or Gemini TTS: script -> audio per scene
image_sourcer.py        # Pexels: image_query -> downloaded stock photo per scene
avatar_generator.py     # OFF by default -- see "Turning the avatar back on"
hyperframes_builder.py  # composites images + captions (+ avatar if enabled) into one HTML scene
pipeline.py             # runs all of the above in order, unattended
.github/workflows/generate-reel.yml   # the "Run workflow" button's logic
```

## Turning the avatar back on

Two ways to run this pipeline:

**Videos without a talking avatar (fully automatic, GitHub Actions):**
follow the setup above. Captions + auto-sourced B-roll + voiceover, zero
manual steps per video. This is the default and it's reliable.

**Videos WITH a talking avatar (needs manual run, but works):** open
`Run_On_Colab.ipynb` in Google Colab (https://colab.research.google.com →
File → Upload notebook). Set the runtime to a free T4 GPU, run the cells
top to bottom — it clones real SadTalker, installs it, and runs it
directly on that GPU using a photo you upload. This replaced an earlier
"hosted" approach (calling a public Hugging Face demo) that proved
unreliable: its real API kept not matching what could be guessed from
outside, and calls could hang indefinitely. Running SadTalker yourself
on a GPU you control is slower to set up (a few minutes per session) but
actually produces a working video, which the hosted route didn't
reliably do.

This is a real trade-off, not a temporary bug: a free, fully-unattended,
reliable talking avatar isn't something either path currently delivers at
once. Pick automatic-without-avatar for daily hands-off videos, or
Colab-with-avatar for when you specifically want the talking-head version
and are fine running a notebook for it.

## Adjusting the look without touching code

Most creative tweaks (caption font size/position, zoom speed, colors)
live in the CSS inside `hyperframes_builder.py`'s `STAGE_TEMPLATE`
string — change a number, commit, done. No need to understand the rest
of the pipeline.

## Language notes

- Kannada, Tamil, Hindi, Telugu, Malayalam, Bengali, Marathi are all
  supported for script + captions (Gemini writes fluently in all of them).
- Voice uses **edge-tts** by default (`config.TTS_BACKEND = "edge"`) —
  free, no API key, no billing, and it auto-detects an available voice for
  whatever locale you set in `config.LANGUAGE` (e.g. `kn-IN`, `ta-IN`).
  This replaced an earlier default of Gemini's native TTS, which hit a
  small per-minute rate limit and then a hard 10-requests/day cap on the
  free tier — not workable for daily automated video generation.
- Captions use fonts that include Kannada/Tamil glyphs by default
  (Noto Sans Kannada / Noto Sans Tamil) so text won't render as boxes.

## Trade-offs to know about

- No talking avatar by default (see above) — captions + B-roll only,
  which is the reliable path right now.
- Pexels' free image library is broad but not infinite — very niche
  topics may get so-so image matches. You can swap in Pixabay/Unsplash
  as alternate free sources (notes are in `image_sourcer.py`).
- HyperFrames is a newer, evolving open-source project — if the render
  step in the workflow fails, check its GitHub repo for current CLI
  syntax and update the render command in `pipeline.py` /
  `generate-reel.yml`.
