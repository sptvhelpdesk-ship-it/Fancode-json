import asyncio
import json
import time
from playwright.async_api import async_playwright

async def get_m3u8():
    async with async_playwright() as p:
        # ব্রাউজার লঞ্চ করা
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()

        print("Opening FanCode Live page...")
        await page.goto("https://www.fancode.com/live-now/all-sports", wait_until="networkidle")

        # লাইভ ম্যাচের লিঙ্কগুলো খুঁজে বের করা
        match_selector = "a[href*='/match/']"
        await page.wait_for_selector(match_selector)
        matches = await page.query_selector_all(match_selector)
        
        match_links = []
        for m in matches[:5]: # আপাতত প্রথম ৫টি লাইভ ম্যাচ চেক করবে
            link = await m.get_attribute('href')
            match_links.append(f"https://www.fancode.com{link}")

        final_data = {"last_updated": time.ctime(), "matches": []}

        # প্রতিটি ম্যাচে ক্লিক করে লিঙ্ক বের করা
        for link in match_links:
            m3u8_url = "Not Found"
            
            # নেটওয়ার্ক মনিটর করা
            def handle_request(request):
                nonlocal m3u8_url
                if ".m3u8" in request.url and "index.m3u8" in request.url:
                    m3u8_url = request.url

            page.on("request", handle_request)

            print(f"Checking Match: {link}")
            await page.goto(link, wait_until="networkidle")
            
            # ৩০-৪০ সেকেন্ড অপেক্ষা করা যাতে অ্যাড শেষ হয় এবং প্লেয়ার লোড হয়
            print("Waiting 40s for Ads and Player...")
            await asyncio.sleep(40) 

            final_data["matches"].append({
                "url": link,
                "m3u8": m3u8_url
            })

        # ডেটা সেভ করা
        with open('fancode.json', 'w') as f:
            json.dump(final_data, f, indent=4)
        
        print("Scraping Complete. Saved to fancode.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_m3u8())
