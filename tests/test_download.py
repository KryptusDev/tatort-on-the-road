from app.downloader import download_video
from app.scraper import find_latest_episode
import logging

logging.basicConfig(level=logging.INFO)

def test():
    # 1. Find episode
    episode = find_latest_episode()
    if not episode:
        print("No episode found.")
        return

    url = episode['url']
    print(f"Downloading: {episode['title']} from {url}")

    # 2. Download
    # We can't easily limit duration with yt-dlp python module without complex options, 
    # so we'll just let it run. It might take a while.
    # Alternatively, we can use a small clip for testing if we had one.
    # But let's just try it.
    
    path = download_video(url, output_dir="testfiles")
    print(f"Downloaded to: {path}")

if __name__ == "__main__":
    test()
