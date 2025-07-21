import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import time

# --- Configuration ---
URL = "https://www.cse.lk/pages/cse-daily/cse-daily.component.html"
DOWNLOAD_FOLDER = "downloads"

URLS_TO_TRY = [
    "https://www.cse.lk/pages/cse-daily/cse-daily.component.html",
    "https://cse.lk/pages/cse-daily/cse-daily.component.html",
    "https://www.cse.lk/pages/cse-daily/"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}

def setup_download_folder():
    """Creates the download folder if it doesn't exist."""
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
        print(f"Created download folder: {DOWNLOAD_FOLDER}")

def fetch_and_download_report():
    """Fetches the webpage and downloads the latest report."""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Try different URLs
    for url in URLS_TO_TRY:
        try:
            print(f"Trying: {url}")
            response = session.get(url, timeout=30)
            response.raise_for_status()
            print(f"✅ Success with: {url}")
            break
        except Exception as e:
            print(f"❌ Failed {url}: {e}")
            continue
    else:
        raise Exception("All URLs failed")
    
    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    report_block = soup.find('div', class_='rules-block')
    
    if not report_block:
        raise Exception("Could not find report block")
    
    # Extract date
    date_element = report_block.find(class_='date')
    if date_element:
        date_text = date_element.get_text().strip()
        print(f"Found date: {date_text}")
        try:
            date_obj = datetime.strptime(date_text, "%d %b %Y")
            filename = f"CSE_Daily_{date_obj.strftime('%Y_%m_%d')}.pdf"
        except:
            filename = f"CSE_Daily_{datetime.now().strftime('%Y_%m_%d')}.pdf"
    else:
        filename = f"CSE_Daily_{datetime.now().strftime('%Y_%m_%d')}.pdf"
    
    # Find download link
    download_link = report_block.find('a', class_='dropdown-button')
    if not download_link:
        raise Exception("Could not find download link")
    
    pdf_url = download_link.get('href')
    if not pdf_url:
        raise Exception("No PDF URL found")
    
    # Handle relative URLs
    if pdf_url.startswith('/'):
        pdf_url = 'https://www.cse.lk' + pdf_url
    elif not pdf_url.startswith('http'):
        pdf_url = 'https://www.cse.lk/pages/cse-daily/' + pdf_url
    
    print(f"Downloading from: {pdf_url}")
    
    # Download PDF
    pdf_response = session.get(pdf_url, timeout=60)
    pdf_response.raise_for_status()
    
    # Save file
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    with open(file_path, 'wb') as f:
        f.write(pdf_response.content)
    
    file_size = len(pdf_response.content)
    print(f"✅ Downloaded: {filename} ({file_size:,} bytes)")
    
    return file_path, filename

def main():
    print("🏢 CSE Daily Report Downloader - GitHub Actions")
    print("=" * 50)
    
    try:
        setup_download_folder()
        file_path, filename = fetch_and_download_report()
        
        print("\n🎉 SUCCESS!")
        print(f"📁 File: {filename}")
        print(f"📍 Location: {file_path}")
        print(f"🕒 Time: {datetime.now()}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
