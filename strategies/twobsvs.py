from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from models import Certificate
from fetcher import fetch_html
from docx import Document
import asyncio
import io

from strategies.base import BaseStrategy

class TwobsvsStrategy(BaseStrategy):
    def __init__(self, max_concurrency):
        super().__init__(max_concurrency)
        self.name = "2bsvs"
        self.url = "https://www.2bsvs.org/certificates/valid-certificates/"
    
    async def find_certificates(self, session, keywords):
        html = await self.parse_html(session)
        relevant_certs = self.get_relevant_certificates(html)

        async def process_cert(cert):
            async with self.semaphore:
                cert_text = (await self.extract_certificate_text(session, cert)).lower()

                matched = [kw for kw in keywords if kw.lower() in cert_text]

                if matched:
                    return {
                        "url": cert.url,
                        "name": cert.name,
                        "products": matched
                    }
                return None

        tasks = [process_cert(cert) for cert in relevant_certs]
        results = await asyncio.gather(*tasks)

        return [r for r in results if r]
            
    
    async def parse_html(self, session):
        base_html = await fetch_html(self.url, session)
        return base_html
    
    def get_relevant_certificates(self, html):
        soup = BeautifulSoup(html, "html.parser")
        
        table = soup.select_one("tbody")
        if not table:
            return []
        
        certs = table.find_all("tr")

        relevant_certs = []

        for cert in certs:
            cert_attributes = cert.find_all("td")
            if len(cert_attributes) != 10:
                continue

            link_tag = cert_attributes[9].find("a")
            if not link_tag:
                continue

            name = cert_attributes[0].get_text(strip=True)
            url = "https://www.2bsvs.org" + link_tag["href"]
            type = cert_attributes[3].get_text(strip=True)
            cert = Certificate(name, url, type)
            
            if(self.is_relevant(cert)):           
                relevant_certs.append(cert)
                
        return relevant_certs
    
    def is_relevant(self, cert):
        return (
            "Trader" in cert.type
        )