import io

from PyPDF2 import PdfReader
import aiohttp
import asyncio

from docx import Document

class BaseStrategy:
    def __init__(self, max_concurrency):
        self.name = "Base"
        self.url = ""
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.should_stop = False
        self.all_tasks = set()
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        
    def find_certificates(self, session, keywords):
        """Return list of raw certificate objects"""
        raise NotImplementedError
    
    def parse_html(self, session):
        """Return HTML for certificate page(s)"""
        raise NotImplementedError

    def is_relevant(self, cert):
        """Trader + valid logic (site-specific wording)"""
        raise NotImplementedError

    def get_certificate_url(self, cert):
        raise NotImplementedError

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
        
        