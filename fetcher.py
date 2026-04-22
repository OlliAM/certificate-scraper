import aiohttp
import asyncio

async def fetch_html(url, session):
    async with session.get(url, headers={"User-Agent": "MyScraper/1.0"}) as response:
        return await response.text()