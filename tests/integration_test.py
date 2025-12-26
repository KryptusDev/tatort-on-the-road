import os
import sys
import logging

# Ensure app module is in path
sys.path.append(os.getcwd())

from app.scraper import find_latest_episode
from app.downloader import download_video

logging.basicConfig(level=logging.INFO)

def test_integration():
    logging.info("Starting integration test...")
    
    # 1. Scrape
    episode = find_latest_episode()
    if not episode:
        logging.error("Scraping failed.")
        return
        
    logging.info(f"Scraped Episode: {episode['title']} ({episode['duration']} Min)")
    
    # 2. Download (Dry run or real?)
    # User wants to verify downloading.
    # We will run it.
    
    url = episode['url']
    logging.info(f"Downloading from: {url}")
    
    # Check if file already exists to avoid re-downloading during dev
    # But downloader doesn't return the exact filename before downloading easily.
    # We'll just let it run. yt-dlp skips if exists usually.
    
    filename = download_video(url, output_dir="testfiles")
    
    if filename and os.path.exists(filename):
        logging.info(f"Download successful: {filename}")
        logging.info(f"File size: {os.path.getsize(filename) / (1024*1024):.2f} MB")
    else:
        logging.error("Download failed.")

if __name__ == "__main__":
    test_integration()
