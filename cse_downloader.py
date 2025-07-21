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

def debug_page_structure(soup):
    """Debug function to examine page structure."""
    print("\n🔍 DEBUGGING PAGE STRUCTURE:")
    print(f"Page title: {soup.title.text if soup.title else 'No title'}")
    
    # Look for common div classes
    divs = soup.find_all('div', class_=True)
    print(f"\nFound {len(divs)} divs with classes:")
    
    class_counts = {}
    for div in divs[:20]:  # Show first 20 divs
        classes = ' '.join(div.get('class', []))
        if classes:
            class_counts[classes] = class_counts.get(classes, 0) + 1
    
    for class_name, count in sorted(class_counts.items())[:15]:
        print(f"  - .{class_name} ({count} times)")
    
    # Look for potential report-related content
    report_keywords = ['daily', 'report', 'cse', 'download', 'pdf']
    print(f"\n📋 Elements containing report keywords:")
    
    for keyword in report_keywords:
        elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())
        if elements:
            print(f"  - '{keyword}': {len(elements)} matches")

def find_report_block(soup):
    """Try multiple selectors to find the report block."""
    selectors_to_try = [
        ('div', {'class_': 'rules-block'}),
        ('div', {'class_': 'daily-report'}),
        ('div', {'class_': 'report-block'}),
        ('div', {'class_': 'cse-daily'}),
        ('section', {'class_': 'daily'}),
        ('div', {'class_': lambda x: x and 'report' in ' '.join(x).lower()}),
        ('div', {'class_': lambda x: x and 'daily' in ' '.join(x).lower()}),
    ]
    
    for tag, attrs in selectors_to_try:
        try:
            element = soup.find(tag, attrs)
            if element:
                print(f"✅ Found report block using: {tag} with {attrs}")
                return element
        except Exception as e:
            print(f"⚠️ Error trying selector {tag}, {attrs}: {e}")
    
    return None

def find_download_link(report_block):
    """Try multiple selectors to find download link."""
    link_selectors = [
        ('a', {'class_': 'dropdown-button'}),
        ('a', {'href': lambda x: x and '.pdf' in x.lower()}),
        ('a', {'class_': lambda x: x and 'download' in ' '.join(x).lower()}),
        ('a', {'class_': lambda x: x and 'pdf' in ' '.join(x).lower()}),
        ('a', {'title': lambda x: x and 'download' in x.lower()}),
    ]
    
    for tag, attrs in link_selectors:
        try:
            link = report_block.find(tag, attrs)
            if link and link.get('href'):
                print(f"✅ Found download link using: {tag} with {attrs}")
                return link
        except Exception as e:
            print(f"⚠️ Error trying link selector {tag}, {attrs}: {e}")
    
    return None

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
    
    # Debug page structure if report block not found
    report_block = find_report_block(soup)
    
    if not report_block:
        print("❌ Could not find report block with any selector")
        debug_page_structure(soup)
        
        # Save page content for manual inspection
        debug_file = os.path.join(DOWNLOAD_FOLDER, 'debug_page.html')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        print(f"💾 Saved page content to {debug_file} for manual inspection")
        
        raise Exception("Could not find report block")
    
    print("✅ Found report block")
    
    # Extract date
    date_element = report_block.find(class_='date')
    if not date_element:
        # Try alternative date selectors
        date_selectors = ['.report-date', '.daily-date', '.date-text', '.pub-date']
        for selector in date_selectors:
            date_element = report_block.select_one(selector)
            if date_element:
                break
    
    if date_element:
        date_text = date_element.get_text().strip()
        print(f"Found date: {date_text}")
        try:
            date_obj = datetime.strptime(date_text, "%d %b %Y")
            filename = f"CSE_Daily_{date_obj.strftime('%Y_%m_%d')}.pdf"
        except ValueError as e:
            print(f"⚠️ Date parsing failed: {e}, using current date")
            filename = f"CSE_Daily_{datetime.now().strftime('%Y_%m_%d')}.pdf"
    else:
        print("⚠️ No date found, using current date")
        filename = f"CSE_Daily_{datetime.now().strftime('%Y_%m_%d')}.pdf"
    
    print(f"Generated filename: {filename}")
    
    # Find download link
    download_link = find_download_link(report_block)
    
    if not download_link:
        print("❌ Could not find download link with any selector")
        
        # Show all links in the report block for debugging
        all_links = report_block.find_all('a')
        print(f"📋 Found {len(all_links)} links in report block:")
        for i, link in enumerate(all_links[:10]):  # Show first 10 links
            href = link.get('href', 'No href')
            text = link.get_text().strip()
            classes = ' '.join(link.get('class', []))
            print(f"  {i+1}. href='{href}' text='{text}' class='{classes}'")
        
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
    
    # Validate PDF content
    if len(pdf_response.content) < 1000:  # Less than 1KB is suspicious
        print(f"⚠️ Warning: Downloaded content is very small ({len(pdf_response.content)} bytes)")
    
    # Save file
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    # Check if file already exists
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime('%H%M%S')
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        print(f"📝 File exists, using new name: {filename}")
    
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
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
