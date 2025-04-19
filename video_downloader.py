import requests
import os
from dotenv import load_dotenv
# Ideally load this from env, e.g. os.environ["VIMEO_TOKEN"]
load_dotenv()

ACCESS_TOKEN = os.getenv('VIMEO_ACCESS_TOKEN')

def download_video(video_id: str) -> str:
    """
    Download the lowest‑res MP4 for the given Vimeo ID.
    Returns the local filename.
    """
    url = f"https://api.vimeo.com/videos/{video_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    download_links = resp.json().get("download", [])
    if not download_links:
        raise RuntimeError("No downloadable links; check Vimeo token scopes.")

    # pick lowest by height
    link = min(download_links, key=lambda L: L.get("height", float("inf")))
    fname = f"{video_id}_{link['quality']}_{link['height']}p.mp4"

    with requests.get(link["link"], stream=True) as r:
        r.raise_for_status()
        with open(fname, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"✅ Downloaded {fname}")
    return fname
