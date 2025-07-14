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
            for item in listings[0:2]:
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
        price_elem = item.select_one('.npPriceBox')
        image_elem = item.select_one('.npFavBtn.shortlistcontainerlink')

        # Extract data with safety checks
        project_id = safe_get_attribute(fav_btn, 'data-projectid')
        project_name = safe_get_text(project_name_elem)
        url = safe_get_attribute(url_elem, 'href')
        location = safe_get_text(location_elem)
        price_range = safe_get_text(price_elem)
        status = safe_get_attribute(fav_btn, 'data-propstatus')
        image = safe_get_attribute(image_elem, 'data-image')

        # Skip if essential data is missing
        if not project_id or not project_name:
            return None
        
        # Extract units information
        units = self._extract_units(item)

        project_spec = self.extract_project_specifications(url)
        amenities = self.extract_amenities(url)
        builder_info = self.extract_builder_information(url)
        property_spec = self.extract_property_specification(url)
        property_about = self.extract_property_about(url)
        price_insights = self.extract_price_insights(url)

        print(f"Extracted {project_id}")

        return {
            'propertyId': project_id,
            'project_name': project_name,
            'location': location,
            'image': "https://static.squareyards.com/" + image if image else None,
            'price': price_range,
            'project_status': status,
            'property_about': property_about,
            'project_spec': project_spec,
            'amenities': amenities,
            'builder_info': builder_info,
            'property_spec': property_spec,
            'price_insights': price_insights,
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


    def extract_project_specifications(self, url):
        """Scrape the details from a property's individual page."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                print(f"Failed to fetch detail page: {url}")
                return {}

            soup = BeautifulSoup(response.text, 'html.parser')

            # Get status box data as array
            status_box_items = soup.select('.status-box li:nth-of-type(3) div.status')
            status_data = []
            for item in status_box_items:
                bhk_type = item.select_one('.unit strong')
                if bhk_type:
                    bhk_type = bhk_type.get_text(strip=True)
                else:
                    bhk_type = None
                status_data.append(bhk_type)  # Debugging line
            
            return {
                'unit_config': status_data[0] if status_data else None,
                'size': status_data[1] if status_data else None,
                'units': status_data[2] if status_data else None,
                'area': status_data[3] if status_data else None,
            }

        except Exception as e:
            print(f"Error scraping detail page {url}: {e}")
            return {}
    
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

    def extract_amenities(self, url):
        """Extract grouped amenities with name and image from the property's page."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                print(f"Failed to fetch amenities page: {url}")
                return {}

            soup = BeautifulSoup(response.text, 'html.parser')
            accordion_items = soup.select('.amenities-modal .accordion-item')

            amenities = {}

            for item in accordion_items:
                # Get category name (e.g., Sports, Safety, etc.)
                category_tag = item.select_one('.accordion-header strong')
                category_name = category_tag.get_text(strip=True) if category_tag else 'Unknown'

                # Prepare list of amenities under this category
                category_amenities = []

                # Find all amenity <td> blocks
                amenity_cells = item.select('td')

                for cell in amenity_cells:
                    name_tag = cell.select_one('span')
                    img_tag = cell.select_one('img')

                    name = name_tag.get_text(strip=True) if name_tag else None
                    image = img_tag.get('data-src') or img_tag.get('src') if img_tag else None

                    if name and image:
                        category_amenities.append({
                            'name': name,
                            'icon': image
                        })

                if category_amenities:
                    amenities[category_name] = category_amenities

            return amenities

        except Exception as e:
            print(f"Error scraping amenities from {url}: {e}")
            return {}

    def extract_builder_information(self, url):
        """Extract builder information from the property's page."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                print(f"Failed to fetch builder information page: {url}")
                return {}

            soup = BeautifulSoup(response.text, 'html.parser')
            builder_info = {}

            # Extract builder name
            builder_name_elem = soup.select_one('section.about-builder-section#aboutBuilder')
            
            builder_name = safe_get_text(builder_name_elem.select_one('h2 a')) if builder_name_elem else None
            builder_image = builder_name_elem.select_one('figure img')
            image = builder_image.get('data-src') or builder_image.get('src') if builder_image else None
            builder_total_projects = safe_get_text(builder_name_elem.select_one('.total-project-list li:nth-of-type(1) strong'))
            builder_experience = safe_get_text(builder_name_elem.select_one('.total-project-list li:nth-of-type(2) strong'))
            builder_description = safe_get_text(builder_name_elem.select_one('.content-box p'))

            builder_info['name'] = builder_name.strip('About - ')
            builder_info['image'] = image.rpartition('?')[0] if '?' in image else image
            builder_info['total_projects'] = builder_total_projects
            builder_info['experience'] = builder_experience
            builder_info['description'] = builder_description

            return builder_info

        except Exception as e:
            print(f"Error scraping builder information from {url}: {e}")
            return {}
        
    def extract_property_specification(self, url):
        """Extract property specifications from the property's page."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                print(f"Failed to fetch property specifications page: {url}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            spec_rows = soup.select('section#specifications table.specification-table tr')

            specifications = []

            for row in spec_rows:
                heading_tag = row.select_one('.specification-heading strong')
                value_tag = row.select_one('.specification-value span')

                if heading_tag and value_tag:
                    title = heading_tag.get_text(strip=True)
                    value = value_tag.get_text(strip=True)

                    specifications.append({
                        "specification_title": title,
                        "specification_value": value
                    })

            return specifications

        except Exception as e:
            print(f"Error scraping property specifications from {url}: {e}")
            return []
        
    def extract_property_about(self, url):
        """Extract property about information from the property's page."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                print(f"Failed to fetch property about page: {url}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            about_element = soup.select_one('section.about-project-section#aboutProject .content-box')

            # Extract text using a helper or directly
            about_info = about_element.decode_contents() if about_element else ""

            return about_info

        except Exception as e:
            print(f"Error scraping property specifications from {url}: {e}")
            return []
        
    def extract_price_insights(self, url):
        """Extract rental and comparable pricing insights from the property's page."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                print(f"Failed to fetch property insights page: {url}")
                return {}

            soup = BeautifulSoup(response.text, 'html.parser')
            insights_section = soup.select_one('section.price-insight-section#dataPriceInsights')

            insights_data = {
                "rentalSupply": [],
                "comparableProjects": []
            }

            # === RENTAL SUPPLY TABLE ===
            rental_rows = insights_section.select(
                'article.rental-supply .rental-supply-table table tbody tr'
            )
            for row in rental_rows:
                cols = row.find_all('td')
                if len(cols) == 3:
                    insights_data["rentalSupply"].append({
                        "configuration": cols[0].get_text(strip=True),
                        "inProject": cols[1].get_text(strip=True),
                        "inSector": cols[2].get_text(strip=True),
                    })

            # === COMPARABLE PROJECTS ===
            comparable_projects = insights_section.select(
                'article.comparable-projects .comparable-projects-item'
            )
            for proj in comparable_projects:
                name_tag = proj.select_one('.comparable-projects-info')
                price_tag = proj.select_one('.comparable-projects-value span')

                if name_tag and price_tag:
                    insights_data["comparableProjects"].append({
                        "project": name_tag.get_text(strip=True),
                        "pricePerSqFt": price_tag.get_text(strip=True),
                    })

            return insights_data

        except Exception as e:
            print(f"Error scraping property insights from {url}: {e}")
            return {}

