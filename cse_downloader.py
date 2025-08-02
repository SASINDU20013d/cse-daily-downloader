import os
import subprocess
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configuration
URL = "https://www.cse.lk/pages/cse-daily/cse-daily.component.html"
DOWNLOAD_FOLDER = "downloads"

def commit_and_push_to_git(file_path):
    """Commits and pushes the downloaded file to the git repository."""
    try:
        print(f"Adding {file_path} to git...")
        
        # Add the downloads folder to git
        subprocess.run(['git', 'add', 'downloads/'], check=True, cwd=os.getcwd())
        
        # Create commit message with current date and filename
        commit_message = f"Add downloaded CSE daily report: {os.path.basename(file_path)} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Commit the changes
        result = subprocess.run(['git', 'commit', '-m', commit_message], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print(f"✅ Successfully committed: {commit_message}")
            
            # Push to remote repository
            print("Pushing to remote repository...")
            push_result = subprocess.run(['git', 'push'], 
                                       capture_output=True, text=True, cwd=os.getcwd())
            
            if push_result.returncode == 0:
                print("✅ Successfully pushed to remote repository!")
            else:
                print(f"⚠️  Push failed: {push_result.stderr}")
                print("File committed locally but not pushed to remote.")
        else:
            if "nothing to commit" in result.stdout:
                print("ℹ️  No changes to commit (file may already exist in repository)")
            else:
                print(f"⚠️  Commit failed: {result.stderr}")
                
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error during git operations: {e}")

def setup_driver():
    """Sets up the Selenium WebDriver for GitHub Actions."""
    options = Options()
    
    # Essential headless options for GitHub Actions
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
        
    print("Setting up WebDriver for GitHub Actions...")
    driver = webdriver.Chrome(options=options)
    return driver

def fetch_and_download_report(driver):
    """Navigates to the URL, finds the report, and downloads it."""
    print(f"Navigating to {URL}...")
    driver.get(URL)
    print("Page navigation complete.")

    try:
        print("Waiting for the daily report section to appear...")
        wait = WebDriverWait(driver, 30)
        report_block = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "rules-block"))
        )
        print("Report section found.")

        # Extract date
        date_element = report_block.find_element(By.CLASS_NAME, "date")
        date_text = date_element.text.strip()
        print(f"Found report date: {date_text}")

        # Create filename
        date_obj = datetime.strptime(date_text, "%d %b %Y")
        new_filename = f"CSE_Daily_{date_obj.strftime('%Y_%m_%d')}.pdf"
        print(f"New filename: {new_filename}")
        
        # Find download link
        download_link_element = report_block.find_element(By.CSS_SELECTOR, "a.dropdown-button")
        pdf_url = download_link_element.get_attribute('href')
        
        if not pdf_url:
            raise ValueError("Could not find the PDF download link.")
            
        print(f"Found PDF download link: {pdf_url}")

        # Download PDF
        print(f"Downloading PDF from link...")
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        print("PDF content downloaded successfully.")

        # Save file with unique name if file exists
        base, ext = os.path.splitext(new_filename)
        file_path = os.path.join(DOWNLOAD_FOLDER, new_filename)
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(DOWNLOAD_FOLDER, f"{base}_{counter}{ext}")
            counter += 1
        print(f"Saving PDF to {file_path}...")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print("-" * 50)
        print(f"✅ SUCCESS: Downloaded report to: {file_path}")
        print(f"📊 Size: {len(response.content):,} bytes")
        print("-" * 50)
        
        # Commit and push to git repository
        commit_and_push_to_git(file_path)

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        # Save page source for debugging
        with open(os.path.join(DOWNLOAD_FOLDER, 'debug_page.html'), 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        raise

def main():
    """Main function to run the script."""
    driver = None
    try:
        driver = setup_driver()
        fetch_and_download_report(driver)
    finally:
        if driver:
            print("Closing WebDriver.")
            driver.quit()

if __name__ == "__main__":
    main()
