import csv
import math
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup

class PaginationHandler:
    def __init__(self, base_url, selector, settings):
        self.base_url = base_url
        self.selector = selector
        self.settings = settings
        self.current_page = 1
        self.total_pages = 1
        self.session = requests.Session()
        
    def detect_pagination(self, soup):
        """Detect pagination pattern from the first page"""
        pagination_links = soup.select(self.settings.get('pagination_selector', 'a[href*="page"]'))
        if pagination_links:
            last_page_link = pagination_links[-1]['href']
            parsed = urlparse(last_page_link)
            query = parse_qs(parsed.query)
            if 'page' in query:
                self.total_pages = int(query['page'][0])
            return True
        return False

    def get_next_page_url(self):
        """Generate URL for the next page"""
        if self.current_page >= self.total_pages:
            return None
            
        parsed = urlparse(self.base_url)
        query = parse_qs(parsed.query)
        query['page'] = [str(self.current_page + 1)]
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def scrape_page(self, url):
        """Scrape a single page"""
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.select(self.selector)

    def scrape_all_pages(self):
        """Scrape all pages"""
        all_data = []
        while self.current_page <= self.total_pages:
            page_data = self.scrape_page(self.base_url)
            all_data.extend(page_data)
            self.current_page += 1
            self.base_url = self.get_next_page_url()
            if not self.base_url:
                break
        return all_data

class CSVExporter:
    @staticmethod
    def export(data, filename, fields=None):
        """Export scraped data to CSV"""
        if not fields:
            fields = ['text', 'href'] if hasattr(data[0], 'href') else ['text']
            
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            for item in data:
                row = {field: getattr(item, field, '') for field in fields}
                writer.writerow(row)