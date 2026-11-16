"""
URP Scraper for RAG-Forge
Scrapes TWU University Regulations & Procedures from a single page.
All 200 policies are loaded in the HTML .
Policy detail pages are PDFs hosted on public.powerdms.com.
"""

import asyncio
import aiohttp
import requests
import ssl
import certifi
import io
import time
from bs4 import BeautifulSoup
from typing import List, Dict
from pypdf import PdfReader

from rag_forge.scrapers.base import BaseScraper


class URPScraper(BaseScraper):
    """
    Scraper for TWU's University Regulations & Procedures (URP) page.
    All policies are on one page — no pagination needed.
    Policy detail pages are PDFs.
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.base_url = config.get('base_url') or config.get('url') or \
            'https://twu.edu/university-policy/university-regulations-procedures/'
        self.max_concurrent = config.get('max_concurrent', 10)
        self.request_delay = config.get('request_delay', 0.5)
        self.policies = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def fetch(self) -> str:
        """Required method for BaseScraper interface."""
        return self.scrape()
        
    def scrape(self) -> str:
        """Main scraping method - returns plain text of all policies."""
        print("Starting URP scraper...")
        
        all_policies = self.get_all_policy_links()
        print(f"Found {len(all_policies)} policies on the page")
        
        self.policies = asyncio.run(self.scrape_all_policies(all_policies))
        
        combined_text = self.combine_policy_texts(self.policies)
        
        successful = sum(1 for p in self.policies if p.get('scrape_status') == 'success')
        print(f"Successfully scraped {successful}/{len(self.policies)} policies")
        print(f"Total combined text length: {len(combined_text)} characters")
        
        return combined_text
    
    def get_all_policy_links(self) -> List[Dict]:
        """Scrape the single page for all policy links."""
        print(f"  Scraping: {self.base_url}")
        
        all_policies = []
        
        try:
            response = requests.get(self.base_url, timeout=15, headers=self.headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table', {'id': 'university'})
            if not table:
                print("    No table found")
                return []
            
            tbody = table.find('tbody')
            rows = tbody.find_all('tr', recursive=False)
            print(f"    Found {len(rows)} rows in the table")
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 6:
                    policy_number = cells[0].get_text(strip=True)
                    
                    link = cells[1].find('a')
                    if link:
                        title = link.get_text(strip=True)
                        url = link.get('href')
                        if url:
                            if url.startswith('//'):
                                url = f"https:{url}"
                            elif url.startswith('/'):
                                url = f"https://twu.edu{url}"
                    else:
                        title = cells[1].get_text(strip=True)
                        url = None
                    
                    all_policies.append({
                        'policy_number': policy_number,
                        'title': title,
                        'url': url,
                        'category': cells[2].get_text(strip=True),
                        'subcategory': cells[3].get_text(strip=True),
                        'policy_owner': cells[4].get_text(strip=True),
                        'applicable_to': cells[5].get_text(strip=True),
                        'full_text': None,
                        'scrape_status': 'pending'
                    })
            
            time.sleep(self.request_delay)
            
        except Exception as e:
            print(f"    Error scraping: {e}")
        
        return all_policies
    
    async def fetch_policy_detail(self, session: aiohttp.ClientSession, 
                                   policy: Dict) -> Dict:
        """Fetch the full text for a single policy URL (HTML or PDF)."""
        if not policy['url']:
            policy['full_text'] = "No URL available"
            policy['scrape_status'] = 'no_url'
            return policy
        
        try:
            async with session.get(policy['url'], timeout=30, headers=self.headers) as response:
                if response.status != 200:
                    policy['full_text'] = f"HTTP Error: {response.status}"
                    policy['scrape_status'] = f'http_{response.status}'
                    return policy
                
                raw = await response.read()
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Check if it's a PDF
                if raw[:4] == b'%PDF' or 'pdf' in content_type:
                    text = self._extract_pdf_text(raw)
                    policy['content_type'] = 'pdf'
                else:
                    # Regular HTML
                    html = raw.decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')
                    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
                        element.decompose()
                    text = soup.get_text(separator='\n', strip=True)
                    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                    policy['content_type'] = 'html'
                
                policy['full_text'] = text
                policy['scrape_status'] = 'success'
                policy['text_length'] = len(text)
                policy['fetched_url'] = policy['url']
                
                return policy
                
        except asyncio.TimeoutError:
            policy['full_text'] = "Timeout error"
            policy['scrape_status'] = 'timeout'
        except Exception as e:
            policy['full_text'] = f"Error: {str(e)}"
            policy['scrape_status'] = 'error'
        
        return policy
    
    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """Extract text from a PDF file."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            result = '\n\n'.join(text_parts)
            if not result.strip():
                return "PDF had no extractable text"
            return result
        except Exception as e:
            return f"PDF extraction error: {str(e)}"
    
    async def scrape_all_policies(self, policies: List[Dict]) -> List[Dict]:
        """Scrape all policy detail pages with concurrency control."""
        print(f"\n  Scraping {len(policies)} policy detail pages...")
        print(f"  Using {self.max_concurrent} concurrent connections")
        
        # Fix SSL certificate issue on macOS
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def fetch_with_semaphore(session, policy):
            async with semaphore:
                await asyncio.sleep(self.request_delay)
                return await self.fetch_policy_detail(session, policy)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [fetch_with_semaphore(session, policy) for policy in policies]
            results = await asyncio.gather(*tasks)
        
        successful = sum(1 for p in results if p.get('scrape_status') == 'success')
        print(f"  Successfully scraped {successful}/{len(results)} policies")
        
        # Show content type breakdown
        pdf_count = sum(1 for p in results if p.get('content_type') == 'pdf')
        html_count = sum(1 for p in results if p.get('content_type') == 'html')
        print(f"  Content types: {pdf_count} PDFs, {html_count} HTML")
        
        # Average text length for successful ones
        successful_texts = [p.get('text_length', 0) for p in results if p.get('scrape_status') == 'success']
        if successful_texts:
            avg_len = sum(successful_texts) / len(successful_texts)
            print(f"  Average text length: {avg_len:.0f} characters")
        
        errors = [p for p in results if p.get('scrape_status') not in ['success', 'pending']]
        if errors:
            print(f"  Errors occurred for {len(errors)} policies")
            for err in errors[:3]:
                print(f"    - {err['policy_number']}: {err.get('scrape_status')}")
                print(f"      {err.get('full_text', '')[:100]}")
        
        return results
    
    def combine_policy_texts(self, policies: List[Dict]) -> str:
        """Combine all policy texts into a single string for the RAG pipeline."""
        combined = []
        
        for policy in policies:
            if policy.get('full_text') and policy.get('scrape_status') == 'success':
                header = f"POLICY {policy['policy_number']}: {policy['title']}"
                header += f"\nCategory: {policy['category']}"
                header += f"\nSubcategory: {policy['subcategory']}"
                header += f"\nPolicy Owner: {policy['policy_owner']}"
                header += f"\nApplicable To: {policy['applicable_to']}"
                header += f"\n---\n"
                
                combined.append(header + policy['full_text'])
        
        return "\n\n".join(combined)