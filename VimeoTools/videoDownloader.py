import os
import requests
from dotenv import load_dotenv

API_BASE = "https://api.vimeo.com"

# Load environment variables from .env file
load_dotenv()
ACCESS_TOKEN = os.getenv("VIMEO_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise RuntimeError("VIMEO_ACCESS_TOKEN not set. Please define it in your .env file.")

def fetch_metadata_as_string(video_id: str) -> str:
    """
    Fetches title & description for a Vimeo video and returns
    them concatenated in a single string.
    """
    url = f"{API_BASE}/videos/{video_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    params = {"fields": "name,description"}

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    title = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()

    return f"Title: {title}\n\nDescription:\n{description}"

def download_video(video_id: str) -> str:
    """
    Download the lowest‑res MP4 for the given Vimeo ID.
    Returns the local filename.
    """
    url = f"{API_BASE}/videos/{video_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    download_links = resp.json().get("download", [])
    if not download_links:
        raise RuntimeError("No downloadable links; check Vimeo token scopes.")

    # Pick the lowest resolution by height
    link = min(download_links, key=lambda L: L.get("height", float("inf")))
    fname = f"{video_id}_{link['quality']}_{link['height']}p.mp4"

    with requests.get(link["link"], stream=True) as r:
        r.raise_for_status()
        with open(fname, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"✅ Downloaded {fname}")
    return fname

def main():
    # Allow the video ID to be provided via env or prompt
    video_id = os.getenv("VIMEO_VIDEO_ID")
    if not video_id:
        video_id = input("Enter Vimeo video ID: ").strip()

    try:
        # Fetch and display metadata
        metadata = fetch_metadata_as_string(video_id)
        print(metadata)

        # Download the video
        filename = download_video(video_id)
        print(f"Downloaded video to: {filename}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()