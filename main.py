import os
import json
import asyncio
import argparse
from urllib.parse import urlparse
from playwright.async_api import async_playwright

def add_url(url):
    file_path = "urls.json"
    data = {"urls": []}
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass
    
    if url not in data["urls"]:
        data["urls"].append(url)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Added URL: {url}")
    else:
        print(f"URL already exists in list: {url}")

async def process_view(browser, url, domain, version, dimensions):
    print(f"  - Generating {version} PDF for {domain}...")
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

async def generate_pdfs():
    try:
        with open("urls.json", "r") as f:
            data = json.load(f)
            urls = data.get("urls", [])
    except FileNotFoundError:
        print("Error: urls.json not found. Use 'add' command first.")
        return

    if not urls:
        print("No URLs found in urls.json.")
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
            
            # Process both desktop and mobile versions simultaneously for this URL
            tasks = [
                process_view(browser, url, domain, version, dimensions)
                for version, dimensions in viewports.items()
            ]
            await asyncio.gather(*tasks)
                    
        await browser.close()

def main():
    parser = argparse.ArgumentParser(description="Webpage to PDF Converter")
    subparsers = parser.add_subparsers(dest="command", help="Commands to run")

    # 'add' command
    parser_add = subparsers.add_parser("add", help="Add a URL to the JSON list")
    parser_add.add_argument("url", type=str, help="The full URL to add")

    # 'run' command
    parser_run = subparsers.add_parser("run", help="Generate PDFs for all URLs in the list")

    args = parser.parse_args()

    if args.command == "add":
        add_url(args.url)
    elif args.command == "run":
        asyncio.run(generate_pdfs())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
