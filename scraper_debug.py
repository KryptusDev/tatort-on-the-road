import requests
from bs4 import BeautifulSoup

url = "https://www.ardmediathek.de/tatort"
try:
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the "Neue Tatorte" headline to locate the section
    # Based on markdown, it was an h2
    header = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3'] and "Neue Tatorte" in tag.text)
    
    if header:
        print(f"Found Header: {header.text}")
        # The slider/list should be the next sibling or inside a container nearby
        # Let's look for links with "Min." in their text in the whole page first to see the pattern
        
        links = soup.find_all('a')
        count = 0
        for link in links:
            text = link.get_text(strip=True)
            if "Min." in text and "/video/" in link.get('href', ''):
                print(f"--- Link {count} ---")
                print(f"Text: {text}")
                print(f"HREF: {link.get('href')}")
                print(f"HTML: {link.prettify()[:200]}...") # Print first 200 chars of HTML
                count += 1
                if count >= 5:
                    break
    else:
        print("Header 'Neue Tatorte' not found.")
        
except Exception as e:
    print(f"Error: {e}")
