import asyncio

import aiohttp

from fetcher import fetch_html
from strategies.registry import STRATEGIES, get_strategy
from pipeline import run_pipeline


async def main():
    keywords = ["manure", "wood pellets", "biodiesel"]
    
    strategies = [cls(max_concurrency=10) for cls in STRATEGIES.values()]
    
    await asyncio.gather(*[run_pipeline(strategy, keywords) for strategy in strategies])


if __name__ == "__main__":
    asyncio.run(main())
