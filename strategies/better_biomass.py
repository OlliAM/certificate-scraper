import asyncio

from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from cache import Cache
from models import Certificate
from fetcher import fetch_html
from docx import Document
import io

from strategies.base import BaseStrategy

class BetterBiomassStrategy(BaseStrategy):
    def __init__(self, max_concurrency):
        super().__init__(max_concurrency)
        self.name = "BetterBiomass"
        self.url = "https://betterbiomass.nl/nl/certificaathouders/"
        self.cache = Cache(f"cache/{self.name}.json")                
        
    async def parse_html(self, session):
        base_html = await fetch_html(self.url, session)
        iframe_url = self.extract_iframe_url(base_html)
        iframe_html = await fetch_html(iframe_url, session)
        return iframe_html
    
    def get_relevant_certificates(self, html):
        soup = BeautifulSoup(html, "html.parser")
        
        table = soup.select_one("tbody")
        if not table:
            return []
        
        certs = table.find_all("tr")

        relevant_certs = []

        for cert in certs:
            cert_attributes = cert.find_all("td")
            if len(cert_attributes) < 10:
                continue

            link_tag = cert_attributes[0].find("a")
            if not link_tag:
                continue

            name = link_tag.get_text(strip=True)
            url = link_tag["href"]
            type = cert_attributes[2].get_text(strip=True)
            status = cert_attributes[7].get_text(strip=True)
            cert = Certificate(name, url, type)
            
            if(self.is_relevant(cert, status)):           
                relevant_certs.append(cert)
                
        return relevant_certs
    
    def is_relevant(self, cert, status):
        return (
            "Trader" in cert.type and
            status == "Valid"
        )
    
    def extract_iframe_url(self, html):
        soup = BeautifulSoup(html, "html.parser")
        
        iframe = soup.find("iframe")
        if not iframe:
            return None
        
        return iframe.get("src")