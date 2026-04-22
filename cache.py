import asyncio
import json
from pathlib import Path


class Cache:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(exist_ok=True)
        self.data = {}
        self.lock = asyncio.Lock()
        if self.filepath.exists():
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def is_fully_checked(self, url, keywords):
        if url not in self.data:
            return False
        checked = self.data[url]["checked"]
        return all(kw in checked for kw in keywords)

    def get_matched(self, url, keywords):
        matched = self.data[url]["matched"]
        return [kw for kw in matched if kw in keywords]

    async def record(self, url, name, checked, matched):
        async with self.lock:
            self.data[url] = {
                "name": name,
                "checked": list(checked),
                "matched": matched
            }
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)