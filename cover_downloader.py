import os
import requests
from PIL import Image
from io import BytesIO

# ---------------- CONFIG ----------------
CACHE_DIR = "cache/covers"  # where images will be saved
CARD_WIDTH = 150
CARD_HEIGHT = 200

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# ---------------- ANILIST QUERY ----------------
ANILIST_API = "https://graphql.anilist.co"
QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    title {
      romaji
    }
    coverImage {
      extraLarge
      large
      medium
    }
  }
}
"""

def download_cover(anime_name: str) -> str | None:
    """
    Query AniList for anime cover, download and save locally.
    Returns local file path if successful, None otherwise.
    """
    # Clean filename
    filename = anime_name.replace(" ", "_") + ".jpg"
    filepath = os.path.join(CACHE_DIR, filename)

    # Skip if already exists
    if os.path.isfile(filepath):
        return filepath

    # Query AniList API
    response = requests.post(ANILIST_API, json={"query": QUERY, "variables": {"search": anime_name}})
    if response.status_code != 200:
        print(f"[Downloader] AniList API error for {anime_name}: {response.status_code}")
        return None

    data = response.json()
    media = data.get("data", {}).get("Media")
    if not media:
        print(f"[Downloader] No AniList entry found for {anime_name}")
        return None

    # Get best available cover
    cover_url = media["coverImage"]["extraLarge"] or media["coverImage"]["large"] or media["coverImage"]["medium"]
    if not cover_url:
        print(f"[Downloader] No cover URL found for {anime_name}")
        return None

    # Download image
    try:
        img_data = requests.get(cover_url).content
        img = Image.open(BytesIO(img_data)).convert("RGB")

        # Resize maintaining aspect ratio
        img.thumbnail((CARD_WIDTH, CARD_HEIGHT))
        # Create background and paste to center
        final_img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0))
        x_offset = (CARD_WIDTH - img.width) // 2
        y_offset = (CARD_HEIGHT - img.height) // 2
        final_img.paste(img, (x_offset, y_offset))

        final_img.save(filepath)
        print(f"[Downloader] Saved cover for {anime_name}")
        return filepath
    except Exception as e:
        print(f"[Downloader] Failed to download {anime_name}: {e}")
        return None

if __name__ == "__main__":
    # Example usage: read anime names from a file or list
    anime_list = ["Tearmoon Empire", "Momentary Lily", "Momokuri"]
    for anime in anime_list:
        download_cover(anime)
