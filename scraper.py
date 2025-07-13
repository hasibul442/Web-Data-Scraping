# Web scraper for Gurgaon properties

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from config import HEADERS, BASE_URL, REQUEST_TIMEOUT
from utils import safe_get_text, safe_get_attribute

class PropertyScraper:
    """A class to scrape property listings from SquareYards."""
    
    def __init__(self, headers=None, base_url=None, timeout=None):
        self.headers = headers or HEADERS
        self.base_url = base_url or BASE_URL
        self.timeout = timeout or REQUEST_TIMEOUT
    
    def scrape_page(self, page):
        """Scrape a single page and return property data."""
        try:
            print(f"Scraping page {page}")
            url = self.base_url + str(page)
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code != 200:
                print(f"Failed to fetch page {page}: Status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('div', class_='npTile')
            
            if not listings:
                print(f"No listings found on page {page}")
                return []

            page_data = []
            for item in listings:
                try:
                    property_data = self._extract_property_data(item)
                    if property_data:
                        page_data.append(property_data)
                except Exception as e:
                    print(f"Error parsing one property on page {page}: {e}")
                    continue
                    
            print(f"Found {len(page_data)} properties on page {page}")
            return page_data
            
        except requests.RequestException as e:
            print(f"Request error scraping page {page}: {e}")
            return []
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            return []

    def _extract_property_data(self, item):
        """Extract property data from a listing item."""
        # Get basic elements
        fav_btn = item.select_one('.npFavBtn')
        project_name_elem = item.select_one('.npProjectName a strong')
        url_elem = item.select_one('.npProjectName a')
        location_elem = item.select_one('.npProjectCity')
        developer_elem = item.select_one('.npDeveloperLogo img')
        price_elem = item.select_one('.npPriceBox')
        
        # Extract data with safety checks
        project_id = safe_get_attribute(fav_btn, 'data-projectid')
        project_name = safe_get_text(project_name_elem)
        url = safe_get_attribute(url_elem, 'href')
        location = safe_get_text(location_elem)
        developer = safe_get_attribute(developer_elem, 'alt')
        price_range = safe_get_text(price_elem)
        status = safe_get_attribute(fav_btn, 'data-propstatus')
        
        # Skip if essential data is missing
        if not project_id or not project_name:
            return None
        
        # Extract units information
        units = self._extract_units(item)
        
        return {
            'propertyId': project_id,
            'project_name': project_name,
            'url': url,
            'location': location,
            'developer': developer,
            'priceRange': price_range,
            'status': status,
            'units': units
        }
    
    def _extract_units(self, item):
        """Extract units information from a property listing."""
        units = []
        unit_rows = item.select('.pTable tbody tr')
        
        for row in unit_rows:
            cols = row.find_all('td')
            if len(cols) == 3:
                units.append({
                    'unit': safe_get_text(cols[0]),
                    'size': safe_get_text(cols[1]),
                    'price': safe_get_text(cols[2])
                })
        
        return units
    
    def scrape_multiple_pages(self, pages, max_workers=10):
        """Scrape multiple pages concurrently."""
        if not pages:
            return []
            
        print(f"Starting to scrape {len(pages)} pages with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            all_pages_data = list(executor.map(self.scrape_page, pages))
        
        # Flatten the results
        results = []
        for page_data in all_pages_data:
            if page_data:
                results.extend(page_data)
        
        return results
