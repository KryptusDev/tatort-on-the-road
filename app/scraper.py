import requests
from bs4 import BeautifulSoup
import logging
import re
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TATORT_PAGE_URL = "https://www.ardmediathek.de/tatort"
BASE_URL = "https://www.ardmediathek.de"

def find_latest_episode():
    """
    Scrapes the ARD Mediathek Tatort page for the latest episode.
    Filters by duration (80-100 minutes) to find full episodes.
    Returns a dictionary with 'url', 'title', 'duration' or None if failed.
    """
    logging.info(f"Scraping {TATORT_PAGE_URL} for latest Tatort episode...")
    
    try:
        response = requests.get(TATORT_PAGE_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links that look like videos
        links = soup.find_all('a', href=True)
        
        candidates = []
        
        for link in links:
            href = link['href']
            if "/video/" not in href:
                continue
                
            text = link.get_text(strip=True)
            
            # Look for duration pattern "89Min." or "90 Min."
            match = re.search(r'(\d+)\s*Min\.', text)
            if match:
                duration = int(match.group(1))
                
                # Filter by duration (90 +/- 10 minutes)
                if 80 <= duration <= 100:
                    # Filter out unwanted versions if possible (though duration usually handles trailers)
                    if "Hörfassung" in text or "Audiodeskription" in text:
                        continue
                        
                    full_url = urljoin(BASE_URL, href)
                    
                    # Extract a cleaner title if possible
                    # The text is often mashed: "89Min.TitleSeries..."
                    # We can try to split by "Min."
                    # text_parts = text.split("Min.")
                    # title_part = text_parts[1] if len(text_parts) > 1 else text
                    
                    # For now, just use the raw text or the href slug as a fallback title
                    title = text
                    
                    candidates.append({
                        'url': full_url,
                        'title': title,
                        'duration': duration
                    })
                    
        if not candidates:
            logging.warning("No matching episodes found.")
            return None
            
        # Return the first one found (assuming page order implies recency/relevance)
        # The "Neue Tatorte" section is usually at the top.
        latest = candidates[0]
        logging.info(f"Found episode: {latest['title']} ({latest['duration']} Min) - {latest['url']}")
        return latest

    except Exception as e:
        logging.error(f"Error in scraper: {e}")
        return None

if __name__ == "__main__":
    # Test run
    episode = find_latest_episode()
    if episode:
        print(f"Result: {episode}")
