import io

from PyPDF2 import PdfReader
import aiohttp
import asyncio
from cache import Cache
from abc import ABC, abstractmethod

from docx import Document

class BaseStrategy(ABC):
    def __init__(self, max_concurrency):
        self.name = "Base"
        self.url = ""
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.should_stop = False
        self.all_tasks = set()
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.cache = Cache(f"cache/{self.name}.json")

    @abstractmethod
    async def parse_html(self, session):
        """Return HTML for certificate page(s)"""
        pass

    @abstractmethod
    def is_relevant(self, cert):
        """Trader + valid logic (site-specific wording)"""
        pass

    @abstractmethod
    def get_relevant_certificates(self, html):
        pass

    async def find_certificates(self, session, keywords):
        html = await self.parse_html(session)
        relevant_certs = self.get_relevant_certificates(html)
        tasks = [self.process_cert(session, cert, keywords) for cert in relevant_certs]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    async def extract_certificate_text(self, session, cert):
        print(f"checking {cert.name} for relevant products")
        headers = {"User-Agent": "Mozilla/5.0"}

        async with session.get(cert.url, headers=headers) as res:
            if res.status != 200:
                return ""
            content_type = res.headers.get("Content-Type", "").lower()
            file_bytes = await res.read()

        if "pdf" in content_type:
            return await asyncio.to_thread(self._parse_pdf, file_bytes)
        elif "wordprocessingml.document" in content_type:
            return await asyncio.to_thread(self._parse_docx, file_bytes)
        else:
            print(f"Unsupported file type: {cert.url} ({content_type})")
            return ""

    def _parse_pdf(self, file_bytes):
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            return "".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""

    def _parse_docx(self, file_bytes):
        try:
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""

    async def process_cert(self, session, cert, keywords):
        async with self.semaphore:
            if self.cache.is_fully_checked(cert.url, keywords):
                matched = self.cache.get_matched(cert.url, keywords)
                return {"url": cert.url, "name": cert.name, "products": matched} if matched else None

            cert_text = (await self.extract_certificate_text(session, cert)).lower()
            matched = [kw for kw in keywords if kw.lower() in cert_text]
            await self.cache.record(cert.url, cert.name, keywords, matched)

            if matched:
                return {"url": cert.url, "name": cert.name, "products": matched}
            return None