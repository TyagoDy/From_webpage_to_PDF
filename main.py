import os
import json
import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright

async def generate_pdfs():
    try:
        with open("urls.json", "r") as f:
            data = json.load(f)
            urls = data.get("urls", [])
    except FileNotFoundError:
        print("Error: urls.json not found.")
        return

    os.makedirs("pdfs", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        viewports = {
            "desktop": {"width": 1920, "height": 1080},
            "mobile": {"width": 375, "height": 812}
        }

        for url in urls:
            print(f"Processing URL: {url}")
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace("www.", "")
            if not domain:
                domain = "unknown_site"
            
            for version, dimensions in viewports.items():
                print(f"  - Generating {version} PDF...")
                
                context = await browser.new_context(
                    viewport=dimensions,
                    device_scale_factor=1
                )
                
                page = await context.new_page()
                
                try:
                    await page.goto(url, wait_until="load", timeout=60000)
                    await page.wait_for_timeout(2000)
                    
                    await page.emulate_media(media="screen")
                    
                    scroll_height = await page.evaluate("document.body.scrollHeight")
                    
                    pdf_filename = f"pdfs/{domain}_{version}.pdf"
                    
                    await page.pdf(
                        path=pdf_filename,
                        width=f"{dimensions['width']}px",
                        height=f"{scroll_height}px",
                        print_background=True,
                        page_ranges="1"
                    )
                    
                    print(f"  - Saved: {pdf_filename}")
                except Exception as e:
                    print(f"  - Error capturing {url} ({version}): {e}")
                finally:
                    await context.close()
                    
        await browser.close()

if __name__ == "__main__":
    asyncio.run(generate_pdfs())
