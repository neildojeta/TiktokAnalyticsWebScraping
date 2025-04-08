# main.py (your original script)

import asyncio
from playwright.async_api import async_playwright
from config import ConfigManager
from scrape_shops import extract_shop_data 
from scrape_creators import extract_creator_data
from scrape_products import extract_product_data

config_manager = ConfigManager()
url = config_manager.url
email = config_manager.email
password = config_manager.password

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Opening Kalodata...")
        await page.goto("https://www.kalodata.com/")

        print("Clicking 'Log in'...")
        await page.click("text=Log in")

        print("Log-in using credentials...")
        # Click the country code dropdown
        await page.wait_for_selector("span.ant-input-group-addon", timeout=10000)
        await page.click("span.ant-input-group-addon")

        # Wait for the country code dropdown to appear
        await page.wait_for_selector(".select-wrapper", timeout=10000)

        # Find all select-wrapper elements
        country_elements = await page.query_selector_all(".select-wrapper")
        for el in country_elements:
            text_content = await el.inner_text()
            if "US +1" in text_content:
                await el.click()
                break

        print("Entering email...")
        await page.wait_for_selector("#register_phone", timeout=10000)
        await page.fill("#register_phone", email)

        print("Entering password...")
        await page.wait_for_selector("#register_password", timeout=10000)
        await page.fill("#register_password", password)

        print("Clicking 'Log in' button...")
        await page.wait_for_selector("button:text('Log in')", timeout=10000)
        await page.click("button:text('Log in')")

        print("Login successful!")

        # Scrape Shop Data
        print("Navigating to shop data...")
        # await extract_shop_data(page)

        # Scrape Creator Data
        print("Navigating to creator data...")
        # await extract_creator_data(page)

        # Scrape Product Data
        print("Navigating to product data...")
        await extract_product_data(page)
        
        await browser.close()

# Run the script
asyncio.run(run())
