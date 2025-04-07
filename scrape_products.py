import asyncio
import pandas as pd
import json

async def extract_creator_data(page):
    print("Clicking 'creator' link inside #page_header_left...")
    await page.click("#page_header_left >> text=Creator")

    print("Waiting for creator data to load...")
    await page.wait_for_selector(".ant-table-row", timeout=10000)

    rows = await page.query_selector_all(".ant-table-row")

    all_creators = []
    all_product_names = []

    for index, row in enumerate(rows):
        #Creator Profile
        creator_name_el = await row.query_selector("div.line-clamp-1:not(.text-base-999)")
        creator_name = await creator_name_el.inner_text() if creator_name_el else "N/A"

        #Creator Name
        type_el = await row.query_selector("div.text-base-999.line-clamp-1")
        type_text = await type_el.inner_text() if type_el else "N/A"

        #Bset Sellers
        image_divs = await row.query_selector_all("div.Component-Image.cover.cover")
        for image_div in image_divs:
            await image_div.hover()
            await asyncio.sleep(0.5)

        product_elements = await page.query_selector_all("span.line-clamp-2")
        for p in product_elements:
            product_name = await p.inner_text()
            normalized_product_name = ' '.join(product_name.split())

            if normalized_product_name not in all_product_names:
                all_product_names.append(normalized_product_name)

        # Revenue
        rev_el = await row.query_selector("td.ant-table-cell.ant-table-column-sort")
        rev_text = await rev_el.inner_text() if rev_el else "N/A"

        td_elements = await row.query_selector_all("td")
        #Followers
        followers = await td_elements[2].inner_text() if td_elements else "N/A"
        #Content Views
        content_views = await td_elements[6].inner_text() if td_elements else "N/A"
        

        creator_data = {
            "Rank": index + 1,
            "Creator Profile": creator_name,
            "Creator Name": type_text,
            "Followers": followers,
            "Best Sellers": [],
            "Revenue": rev_text,
            "Content Views": content_views
        }

        all_creators.append(creator_data)

    for i in range(len(all_creators)):
        start = i * 3
        end = start + 3
        all_creators[i]["Best Sellers"] = all_product_names[start:end]

    # Display results
    for i, creator in enumerate(all_creators):
        print(f"\nCreator {i + 1}:")
        print(f"  Profile: {creator['Creator Profile']}")
        print(f"  Creator Name: {creator['Creator Name']}")
        print(f"  Followers: {creator['Followers']}")
        print(f"  Best Sellers: {', '.join(creator['Best Sellers']) if creator['Best Sellers'] else 'None'}")
        print(f"  Revenue: {creator['Revenue']}")
        print(f"  Content Views: {creator['Content Views']}")

    # Save to CSV
    df = pd.DataFrame(all_creators)
    df["Best Sellers"] = df["Best Sellers"].apply(lambda x: ', '.join(x))
    df.to_csv("top_creators_output.csv", index=False)

    # Save to JSON
    with open("top_creators_output.json", "w", encoding="utf-8") as f:
        json.dump(all_creators, f, ensure_ascii=False, indent=4)
