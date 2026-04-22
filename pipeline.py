from dataclasses import asdict
import json
from pathlib import Path

import aiohttp

from fetcher import fetch_html

async def run_pipeline(strategy, keywords):
    connector = aiohttp.TCPConnector(limit=20)

    async with aiohttp.ClientSession(connector=connector) as session:
        print(f"Starting scrape of {strategy.url}")
        certs = await strategy.find_certificates(session, keywords)
        print("Scraping finished!")
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        output_path = results_dir / f"{strategy.name}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(certs, f, indent=2, ensure_ascii=False)

        print(f"Saved to {output_path}")