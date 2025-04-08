import asyncio
import pandas as pd
import json
import os
import re
import requests

output_dir = "Top_Products/best_selling_products_images"
logo_dir = "Top_Products/product_logo"
trend_dir = "Top_Products/trend_images"
highest_revenue_dir = "Top_Products/highest_revenue_videos"

os.makedirs(output_dir, exist_ok=True)
os.makedirs(logo_dir, exist_ok=True)
os.makedirs(trend_dir, exist_ok=True)
os.makedirs(highest_revenue_dir, exist_ok=True)

async def extract_product_data(page):
    print("Clicking 'product' link inside #page_header_left...")
    await page.click("#page_header_left >> text=Product")

    print("Waiting for product data to load...")
    await page.wait_for_selector(".ant-table-row", timeout=10000)

    rows = await page.query_selector_all(".ant-table-row")

    all_products = []
    all_product_names = []
    image_counter = 1
    logo_counter = 1
    trend_counter = 1

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.kalodata.com"
    }

    for index, row in enumerate(rows):
        # ✅ product Logo
        logo_el = await row.query_selector("div.Component-Image.w-\\[72px\\].h-\\[72px\\].w-\\[72px\\].h-\\[72px\\]")
        product_logo_filename = "N/A"
        if logo_el:
            style = await logo_el.get_attribute("style")
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if match:
                logo_url = match.group(1)
                try:
                    response = requests.get(logo_url, headers=headers)
                    if response.status_code == 200:
                        product_logo_filename = f"product_logo_{logo_counter}.png"
                        with open(os.path.join(logo_dir, product_logo_filename), "wb") as f:
                            f.write(response.content)
                        print(f"✅ Saved logo {product_logo_filename}")
                        logo_counter += 1
                    else:
                        print(f"❌ Failed to download logo image (status {response.status_code})")
                except Exception as e:
                    print(f"❌ Error downloading logo {logo_url}: {e}")

        # product Profile
        product_name_el = await row.query_selector("div.line-clamp-2:not(.text-\\[13px\\]):not(.font-medium)")
        product_name = await product_name_el.inner_text() if product_name_el else "N/A"

        # product Name
        p_range_el = await row.query_selector("div.text-\\[13px\\].font-medium.line-clamp-2")
        p_range_text = await p_range_el.inner_text() if p_range_el else "N/A"


        # Best Sellers (hover and extract image + video)
        image_divs = await row.query_selector_all("div.Component-Image.Layout-VideoCover.cover.Layout-VideoCover.cover")
        best_seller_images = []

        for image_div in image_divs:
            await image_div.hover()
            await asyncio.sleep(3)

            image_name = f"product_{index+1}_image_{image_counter}.png"
            image_path = os.path.join(output_dir, image_name)

            # Save thumbnail image
            style = await image_div.get_attribute("style")
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if match:
                url = match.group(1)
                try:
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        with open(image_path, "wb") as f:
                            f.write(response.content)
                        best_seller_images.append(image_name)
                        if image_name not in all_product_names:
                            all_product_names.append(image_name)
                        print(f"✅ Saved {image_name}")
                        image_counter += 1
                    else:
                        print(f"❌ Failed to download image (status {response.status_code})")
                except Exception as e:
                    print(f"❌ Error downloading {url}: {e}")

            # Save video from file dialog
            try:
                async with page.expect_download() as download_info:
                    await page.click("text=Download Video (Without Watermark)")
                download = await download_info.value
                video_filename = image_name.replace(".png", ".mp4")
                video_path = os.path.join(highest_revenue_dir, video_filename)
                await download.save_as(video_path)
                print(f"🎥 Saved video: {video_filename}")
            except Exception as e:
                print(f"❌ Error downloading video: {e}")

        td_elements = await row.query_selector_all("td")

        # Revenue
        rev_el = await row.query_selector("td.ant-table-cell.ant-table-column-sort")
        rev_text = await rev_el.inner_text() if rev_el else "N/A"

        # Item Sold
        item_sold = await td_elements[4].inner_text() if len(td_elements) > 4 else "N/A"
        # Average Unit Price
        avg_unit_price = await td_elements[5].inner_text() if len(td_elements) > 5 else "N/A"
        # Commission Rate
        commission_rate = await td_elements[6].inner_text() if len(td_elements) > 6 else "N/A"
        # Creator Number
        creator_number = await td_elements[8].inner_text() if len(td_elements) > 8 else "N/A"
        # Launch Date
        launch_date = await td_elements[9].inner_text() if len(td_elements) > 9 else "N/A"
        # Creator Conversion Rate
        creator_conversion_rate = await td_elements[10].inner_text() if len(td_elements) > 10 else "N/A"

        # Revenue Trend Screenshot (5th td)
        revenue_trend_filename = "N/A"
        if len(td_elements) > 3:
            try:
                revenue_trend_filename = f"revenue_trend_{trend_counter}.png"
                await td_elements[3].screenshot(path=os.path.join(trend_dir, revenue_trend_filename))
                print(f"✅ Screenshot saved for revenue trend: {revenue_trend_filename}")
            except Exception as e:
                print(f"❌ Error capturing screenshot for revenue trend: {e}")

        trend_counter += 1

        product_data = {
            "Rank": index + 1,
            "Product Logo": product_logo_filename,
            "Product Name": product_name,
            "Product Range": p_range_text,
            "Revenue": rev_text,
            "Revenue Trend": revenue_trend_filename,
            "Item Sold": item_sold,
            "Average Unit Price": avg_unit_price,
            "Commission Rate": commission_rate,
            "Highest Revenue Videos": [],
            "Highest Revenue Videos Images": best_seller_images,
            "Creator Number": creator_number,
            "Launch Date": launch_date,
            "Creator Conversion Rate": creator_conversion_rate
        }

        all_products.append(product_data)

    for i in range(len(all_products)):
        start = i * 3
        end = start + 3
        all_products[i]["Highest Revenue Videos"] = all_product_names[start:end]

    # Display results
    for i, product in enumerate(all_products):
        print(f"\nproduct {i + 1}:")
        for k, v in product.items():
            print(f"  {k}: {v}")

    # Save to CSV
    df = pd.DataFrame(all_products)
    df["Highest Revenue Videos"] = df["Highest Revenue Videos"].apply(lambda x: ', '.join(x))
    df["Highest Revenue Videos Images"] = df["Highest Revenue Videos Images"].apply(lambda x: ', '.join(x))
    df.to_csv("Top_products/top_products_output.csv", index=False)

    # Save to JSON
    with open("Top_products/top_products_output.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)
