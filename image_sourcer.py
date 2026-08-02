"""
Step: script.json (with image_query per scene) -> output/images/scene_N.jpg

Uses the Pexels API to automatically find and download a matching free
stock photo for each scene -- no manual image picking.

Pexels is free: get an API key at https://www.pexels.com/api/ (instant,
no credit card, generous rate limit). Put it in .env as PEXELS_API_KEY.

Alternative free sources if you want to swap providers:
  - Pixabay API: https://pixabay.com/api/docs/ (also free, no attribution
    required on their standard license)
  - Unsplash API: https://unsplash.com/developers (free tier, requires
    attribution per their license -- keep that in mind for public posting)
"""
import json
import os

import requests

import config

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


def fetch_image_for_query(query: str, out_path: str, api_key: str):
    resp = requests.get(
        PEXELS_SEARCH_URL,
        headers={"Authorization": api_key},
        params={"query": query, "per_page": 1, "orientation": "portrait"},
        timeout=20,
    )
    resp.raise_for_status()
    results = resp.json().get("photos", [])
    if not results:
        raise RuntimeError(f"No stock image found for query: '{query}'")

    # 'portrait' size is a good match for 9:16 reels
    image_url = results[0]["src"]["portrait"]
    img_resp = requests.get(image_url, timeout=30)
    img_resp.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(img_resp.content)


def source_all_images(script: dict = None) -> list[str]:
    if script is None:
        with open(os.path.join(config.OUTPUT_DIR, "script.json"), encoding="utf-8") as f:
            script = json.load(f)

    api_key = os.environ["PEXELS_API_KEY"]

    images_dir = os.path.join(config.OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)

    paths = []
    for scene in script["scenes"]:
        out_path = os.path.join(images_dir, f"scene_{scene['id']}.jpg")
        fetch_image_for_query(scene["image_query"], out_path, api_key)
        print(f"[image_sourcer] scene {scene['id']} ('{scene['image_query']}') -> {out_path}")
        paths.append(out_path)

    return paths


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    source_all_images()
