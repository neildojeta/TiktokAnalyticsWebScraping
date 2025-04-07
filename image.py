from playwright.sync_api import sync_playwright
import requests
import re
import os

output_dir = "kalodata_images"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.kalodata.com/shop", timeout=60000)
    page.wait_for_selector('div[style*="background-image"]')

    image_urls = []
    divs = page.query_selector_all('div[style*="background-image"]')

    for div in divs:
        style = div.get_attribute('style')
        match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
        if match:
            image_urls.append(match.group(1))

    print(f"Found {len(image_urls)} images. Downloading...")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.kalodata.com"
    }

    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                with open(os.path.join(output_dir, f"image_{i+1}.png"), "wb") as f:
                    f.write(response.content)
                print(f"✅ Saved image_{i+1}.png")
            else:
                print(f"❌ Failed to download image {i+1} (status {response.status_code})")
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")

    browser.close()
