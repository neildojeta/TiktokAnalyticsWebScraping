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
    await page.click("#page_header_left >> text=Video & Ad")

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
        product_el = await row.query_selector("div.Component-Image.cover.cover")
        product_image_filename = "N/A"
        if product_el:
            style = await product_el.get_attribute("style")
            match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if match:
                logo_url = match.group(1)
                try:
                    response = requests.get(logo_url, headers=headers)
                    if response.status_code == 200:
                        product_image_filename = f"product_logo_{logo_counter}.png"
                        with open(os.path.join(logo_dir, product_image_filename), "wb") as f:
                            f.write(response.content)
                        print(f"✅ Saved product {product_image_filename}")
                        logo_counter += 1
                    else:
                        print(f"❌ Failed to download product image (status {response.status_code})")
                except Exception as e:
                    print(f"❌ Error downloading product {logo_url}: {e}")

        # Product Names
        product_element = await page.query_selector_all("span.line-clamp-2")
        for p in product_element:
            product_name = await p.inner_text()
            normalized_product_name = ' '.join(product_name.split())

            if normalized_product_name not in all_product_names:
                all_product_names.append(normalized_product_name)

        # product Profile
        video_name_el = await row.query_selector("div.group-hover:text-primary")
        video_name = await video_name_el.inner_text() if video_name_el else "N/A"

        # product Name
        v_duration_el = await row.query_selector("div.text.truncate.text-\\[\\#999\\].text-\\[12px\\]")
        v_duration_text = await v_duration_el.inner_text() if v_duration_el else "N/A"


        # Best Sellers (hover and extract image + video)
        image_divs = await row.query_selector_all("div.Component-Image.Layout-VideoCover.poster.Layout-VideoCover.poster")
        video_content_image = None

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
                        video_content_image = image_name
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

        # Item Sold
        item_sold = await td_elements[3].inner_text() if len(td_elements) > 3 else "N/A"
        # Revenue
        rev_el = await row.query_selector("td.ant-table-cell ant-table-column-sort")
        rev_text = await rev_el.inner_text() if rev_el else "N/A"
        # Average Unit Price
        views_num = await td_elements[6].inner_text() if len(td_elements) > 6 else "N/A"
        # GPM
        gpm = await td_elements[8].inner_text() if len(td_elements) > 8 else "N/A"
        # CPA
        adCPA = await td_elements[9].inner_text() if len(td_elements) > 9 else "N/A"
        # adViewRatio
        adViewRatio = await td_elements[10].inner_text() if len(td_elements) > 10 else "N/A"
        # adSpend
        adSpend = await td_elements[11].inner_text() if len(td_elements) > 11 else "N/A"
        # For Ad Roas
        adRoas = await td_elements[12].inner_text() if len(td_elements) > 12 else "N/A"

        # Revenue Trend Screenshot (5th td)
        revenue_trend_filename = "N/A"
        if len(td_elements) > 5:
            try:
                revenue_trend_filename = f"revenue_trend_{trend_counter}.png"
                await td_elements[5].screenshot(path=os.path.join(trend_dir, revenue_trend_filename))
                print(f"✅ Screenshot saved for revenue trend: {revenue_trend_filename}")
            except Exception as e:
                print(f"❌ Error capturing screenshot for revenue trend: {e}")

        if len(td_elements) > 7:
            try:
                views_trend_filename = f"views_trend_{trend_counter}.png"
                await td_elements[7].screenshot(path=os.path.join(trend_dir, views_trend_filename))
                print(f"✅ Screenshot saved for views trend: {views_trend_filename}")
            except Exception as e:
                print(f"❌ Error capturing screenshot for views trend: {e}")

        trend_counter += 1

        product_data = {
            "Rank": index + 1,
            "Video Content": video_content_image,
            "Video Name": video_name,
            "Video Duration": v_duration_text,
            "Product Image": product_name,
            "Item Sold": item_sold,
            "Revenue": rev_text,
            "Revenue Trend": revenue_trend_filename,
            "Views:": views_num,
            "Views Trend": views_trend_filename,
            "GPM": gpm,
            "Ad CPA": adCPA,
            "Ad View Ratio": adViewRatio,
            "Ad Spend": adSpend,
            "Ad Roas": adRoas,
        }

        all_products.append(product_data)

    for i in range(len(all_products)):
        start = i * 1
        end = start + 1
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
    df.to_csv("Top_Videos/top_videos_output.csv", index=False)

    # Save to JSON
    with open("Top_Videos/top_videos_output.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)
