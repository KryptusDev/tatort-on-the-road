import logging
import subprocess
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_video(url, output_dir="testfiles"):
    """
    Downloads the video from the given URL using yt-dlp.
    Target quality: 720p (approx 1280x720).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    logging.info(f"Downloading video from {url} to {output_dir}...")
    
    # Format selection: Best video with height <= 720 + best audio
    # Output template: tatort_[id].mp4
    output_template = os.path.join(output_dir, "tatort_%(id)s.%(ext)s")
    
    # Format selection: Prefer HTTP (progressive) 720p to avoid ffmpeg merging
    # Filter out audio description and sign language if possible via format selection, 
    # but 'best' usually picks the standard one.
    # We use [protocol^=http] to ensure we get the mp4 file directly.
    cmd = [
        "python", "-m", "yt_dlp",
        "-f", "best[height=720][protocol^=http]",
        "-o", output_template,
        url
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logging.info("Download complete.")
        
        # Find the downloaded file
        # Since we don't know the ID upfront easily without parsing, we can look for the most recent file in the dir
        # or parse the output. 
        # But yt-dlp output template is predictable if we knew the ID.
        # Let's return the path of the downloaded file.
        # A simple way is to list files in output_dir and find the one matching the pattern or just downloaded.
        
        # Better: use --print filename to get the filename
        result = subprocess.run(
            ["python", "-m", "yt_dlp", "--get-filename", "-o", output_template, url],
            capture_output=True, text=True, check=True
        )
        filename = result.stdout.strip()
        return filename
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Download failed: {e}")
        return None

if __name__ == "__main__":
    # Test run
    # Use a known URL or one found by scraper
    test_url = "https://www.ardmediathek.de/video/tatort/tatort-unsichtbar/das-erste/Y3JpZDovL21kci5kZS9iZWl0cmFnL2Ntcy84NGEwOWI4ZS01Y2FmLTRiNDAtYjQ1My1iN2UyOTQxZmMwOGQ" # Example
    # download_video(test_url)
    pass
