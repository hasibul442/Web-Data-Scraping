# Web scraper for Gurgaon properties

import time
import traceback
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from core.config import HEADERS, BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
from media.media_extractor import extract_media_by_sub_tab
from scrapers.builder_information import extract_builder_information
from utils.utils import safe_get_text, safe_get_attribute
from scrapers.location_insights_scraper import extract_location_insights
import re
from tqdm import tqdm
import json
import os
from datetime import datetime
import os

class PropertyScraper:
    """A class to scrape property listings from SquareYards."""
    
    def __init__(self, headers=None, base_url=None, timeout=None):
        self.headers = headers or HEADERS
        self.base_url = base_url or BASE_URL
        self.timeout = timeout or REQUEST_TIMEOUT
        # Collections for unique builders and location insights
        self.builders_collection = {}
        self.location_insights_collection = {}
        self.builder_id_counter = 1
        self.location_id_counter = 1
        # Failed items tracking
        self.failed_items = []
        self.failed_items_file = "output/failed_items.json"
        # Builder error tracking
        self.builder_errors = []
        self.builder_errors_file = "output/builder_errors.json"
    
    def _validate_soup(self, soup, method_name, url=None):
        """Helper method to validate soup and log appropriate errors."""
        if soup is None:
            error_msg = f"[ERROR] No soup available for {method_name}"
            if url:
                error_msg += f" from {url}"
            print(error_msg)
            return False
        return True
    
    def _track_failed_item(self, item, page_number, item_index, error_reason, url=None):
        """Track failed items for later retry."""
        failed_item = {
            "page_number": page_number,
            "item_index": item_index,
            "project_id": safe_get_attribute(item.select_one('.npFavBtn'), 'data-projectid'),
            "project_name": safe_get_text(item.select_one('.npProjectName a strong')),
            "url": url or safe_get_attribute(item.select_one('.npProjectName a'), 'href'),
            "error_reason": error_reason,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_item_html": str(item)  # Store raw HTML for retry
        }
        self.failed_items.append(failed_item)
        print(f"[FAILED ITEM] Tracked: {failed_item['project_name']} - {error_reason}")
    
    def _save_failed_items(self):
        """Save failed items to JSON file."""
        if self.failed_items:
            os.makedirs(os.path.dirname(self.failed_items_file), exist_ok=True)
            
            # Load existing failed items if file exists
            existing_failed = []
            if os.path.exists(self.failed_items_file):
                try:
                    with open(self.failed_items_file, 'r', encoding='utf-8') as f:
                        existing_failed = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load existing failed items: {e}")
            
            # Merge with new failed items
            all_failed = existing_failed + self.failed_items
            
            # Remove duplicates based on project_id and url
            unique_failed = []
            seen = set()
            for item in all_failed:
                key = (item.get('project_id'), item.get('url'))
                if key not in seen:
                    unique_failed.append(item)
                    seen.add(key)
            
            with open(self.failed_items_file, 'w', encoding='utf-8') as f:
                json.dump(unique_failed, f, indent=2, ensure_ascii=False)
            
            print(f"[FAILED ITEMS] Saved {len(self.failed_items)} new failed items to {self.failed_items_file}")
            print(f"[FAILED ITEMS] Total unique failed items: {len(unique_failed)}")
        else:
            print("[FAILED ITEMS] No failed items to save")
    
    def _track_builder_error(self, project_name, project_id, url, error_reason, page_number=None, item_index=None):
        """Track builder information extraction errors."""
        builder_error = {
            "page_number": page_number,
            "item_index": item_index,
            "project_id": project_id,
            "project_name": project_name,
            "url": url,
            "error_reason": error_reason,
            "error_type": "builder_information_error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.builder_errors.append(builder_error)
    
    def _save_builder_errors(self):
        """Save builder errors to JSON file."""
        if self.builder_errors:
            os.makedirs(os.path.dirname(self.builder_errors_file), exist_ok=True)
            
            # Load existing builder errors to avoid duplicates
            existing_errors = []
            if os.path.exists(self.builder_errors_file):
                try:
                    with open(self.builder_errors_file, 'r', encoding='utf-8') as f:
                        existing_errors = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_errors = []
            
            # Combine and deduplicate builder errors
            all_errors = existing_errors + self.builder_errors
            unique_errors = []
            seen = set()
            for error in all_errors:
                key = (error.get('project_id'), error.get('url'), error.get('error_reason'))
                if key not in seen:
                    unique_errors.append(error)
                    seen.add(key)
            
            with open(self.builder_errors_file, 'w', encoding='utf-8') as f:
                json.dump(unique_errors, f, indent=2, ensure_ascii=False)
            
            print(f"[BUILDER ERRORS] Saved {len(self.builder_errors)} new builder errors to {self.builder_errors_file}")
            print(f"[BUILDER ERRORS] Total unique builder errors: {len(unique_errors)}")
        else:
            print("[BUILDER ERRORS] No builder errors to save")
    
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
            for item_index, item in enumerate(tqdm(listings)):
                try:
                    property_data = self._extract_property_data(item, page, item_index)
                    if property_data:
                        page_data.append(property_data)
                except Exception as e:
                    error_reason = f"Error parsing property: {str(e)}"
                    print(f"Error parsing one property on page {page} (index {item_index}): {e}")
                    traceback.print_exc()
                    self._track_failed_item(item, page, item_index, error_reason)
                    continue
                    
            print(f"Found {len(page_data)} properties on page {page}")
            return page_data
            
        except requests.RequestException as e:
            print(f"Request error scraping page {page}: {e}")
            return []
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
            return []

    def _get_or_create_builder_id(self, builder_info):
        """Get existing builder ID or create new one for unique builders using builder_info['id']."""
        if not builder_info or not builder_info.get('id'):
            return None

        builder_id = builder_info['id']

        if builder_id not in self.builders_collection:
            self.builders_collection[builder_id] = builder_info

        return builder_id
    
    def _get_or_create_location_id(self, location_insights):
        """Get existing location ID or create new one for unique locations."""
        if not location_insights or not location_insights.get('url'):
            return None
        
        location_url = location_insights['url']
        
        # Check if location already exists
        for location_id, existing_location in self.location_insights_collection.items():
            if existing_location.get('url') == location_url:
                return location_id
        
        # Create new location entry
        location_id = f"location_{self.location_id_counter}"
        self.location_insights_collection[location_id] = {
            'id': location_id,
            **location_insights
        }
        self.location_id_counter += 1
        return location_id
        

    def _extract_property_data(self, item, page_number=None, item_index=None):
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
            if page_number is not None and item_index is not None:
                self._track_failed_item(item, page_number, item_index, 
                                      "Missing essential data (project_id or project_name)", url)
            return None

        soup = self.get_soup(url)  # Call only once per page
        
        # If soup is None (failed to fetch page), track and skip this property
        if soup is None:
            error_reason = f"Failed to fetch property page: {url}"
            print(f"[WARNING] Skipping property {project_name} due to failed page fetch: {url}")
            if page_number is not None and item_index is not None:
                self._track_failed_item(item, page_number, item_index, error_reason, url)
            return None
            
        project_spec = self.extract_project_specifications(soup, url)
        amenities = self.extract_amenities(soup, url)
        
        # Use the class method for builder info with error handling
        try:
            builder_info = extract_builder_information(soup, url)
            
            # Check if builder_info contains an error and track it
            if isinstance(builder_info, dict) and "error" in builder_info:
                self._track_builder_error(
                    project_name=project_name,
                    project_id=project_id,
                    url=url,
                    error_reason=builder_info["error"],
                    page_number=page_number,
                    item_index=item_index
                )
                # Set builder_info to empty dict for further processing
                builder_info = {}
                
        except Exception as e:
            # Catch any unexpected errors in builder information extraction
            error_msg = f"Error scraping builder information from {url}: {str(e)}"
            self._track_builder_error(
                project_name=project_name,
                project_id=project_id,
                url=url,
                error_reason=error_msg,
                page_number=page_number,
                item_index=item_index
            )
            builder_info = {}
        
        builder_info_basic = self.extract_builder_information_basic(soup, url)
        property_spec = self.extract_property_specification(soup, url)
        property_about = self.extract_property_about(soup, url)
        price_insights = self.extract_price_insights(soup, url)
        nearby_landmarks = self.extract_nearby_landmarks(soup, url)
        faq = self.extract_faq(soup, url)
        price_list = self.extract_price_list(soup)
        rera = self.extract_rera_details(soup)
        floor_plan = self.extract_floor_plans(soup)
        # all_media = extract_media_by_sub_tab(project_id, url)
        location_insights_basic = self.extract_location_description_and_insights(soup)
        detailed_location_insights = extract_location_insights(location_insights_basic["know_more_url"]) if location_insights_basic and location_insights_basic.get("know_more_url") else None
        cordinates = self.extract_coordinates(soup, url)
        # Get or create IDs for builder and location
        builder_id = self._get_or_create_builder_id(builder_info)
        location_id = self._get_or_create_location_id(detailed_location_insights)

        # Ensure location_id is the first key in the dictionary
        if location_insights_basic is None:
            location_insights_basic = {}
        location_insights_basic = {'location_id': location_id, **location_insights_basic}

        # Ensure builder_id is the first key in the dictionary
        if builder_info_basic is None:
            builder_info_basic = {}
        builder_info_basic = {'builder_id': builder_id, **builder_info_basic}

        return {
            'property_id': project_id,
            'name': project_name,
            'location': location,
            'cordinates': cordinates,  # Extracted longitude and latitude coordinates
            'thumbnail_image': "https://static.squareyards.com/" + image if image else None,
            'price': price_range,
            'price_insights': price_insights,
            'status': status,
            "information": project_spec,
            'price_list': price_list,
            'floor_plans': floor_plan,
            'amenities': amenities,
            'specifications': property_spec,
            'about': property_about,
            'nearby_landmarks': nearby_landmarks,
            'location_insights': location_insights_basic,  # Reference to location insights
            'rera': rera,
            'faq': faq,
            'builder_info': builder_info_basic,  # Reference to builder info
            # 'all_media': all_media,
        }
    
    def get_soup(self, url):
        """Reusable method to perform GET request and return parsed HTML soup with retry logic."""
        import time
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                else:
                    print(f"[ERROR] Failed to fetch page: {url} | Status Code: {response.status_code} | Attempt {attempt + 1}/{MAX_RETRIES}")
            except (requests.RequestException, requests.ConnectTimeout, requests.ReadTimeout) as e:
                print(f"[EXCEPTION] While fetching {url} (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"[RETRY] Waiting {RETRY_DELAY} seconds before retry...")
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                print(f"[UNEXPECTED ERROR] While fetching {url}: {e}")
                break
                
        print(f"[FAILED] All {MAX_RETRIES} attempts failed for URL: {url}")
        return None
        
    def scrape_multiple_pages(self, pages, max_workers=10):
        """Scrape multiple pages concurrently."""
        if not pages:
            return {}
            
        print(f"Starting to scrape {len(pages)} pages with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            all_pages_data = list(executor.map(self.scrape_page, pages))
        
        # Flatten the results to get all projects
        projects = []
        for page_data in all_pages_data:
            if page_data:
                projects.extend(page_data)
        
        # Save failed items to JSON file
        self._save_failed_items()
        
        # Save builder errors to JSON file
        self._save_builder_errors()
        
        # Return structured output
        return {
            'projects': projects,
            'builders': list(self.builders_collection.values()),
            'locations': list(self.location_insights_collection.values())
        }

    def extract_project_specifications(self, soup, url):
        """Scrape the details from a property's individual page."""
        if not self._validate_soup(soup, "extract_project_specifications", url):
            return {}
            
        try:
            # Get status box data as array
            overview = {}

            # Get the status box list
            status_box = soup.select_one(".left-side .status-box")
            if not status_box:
                return None
            
            # Third <li>: Unit Config, Size, Number of Units, Total Area
            unit_config = status_box.select_one("li:nth-of-type(3) .status:nth-of-type(1) .bhk-type")
            size = status_box.select_one("li:nth-of-type(3) .status:nth-of-type(2) strong")
            number_of_units = status_box.select_one("li:nth-of-type(3) .status:nth-of-type(3) strong")
            total_area = status_box.select_one("li:nth-of-type(3) .status:nth-of-type(4) strong")

            overview["unit_config"] = unit_config.get_text(strip=True) if unit_config else None
            overview["size"] = re.sub(r'\s+', ' ', size.get_text(strip=True)) if size else None
            overview["units"] = number_of_units.get_text(strip=True) if number_of_units else None
            overview["total_area"] = total_area.get_text(strip=True) if total_area else None

            return overview

        except Exception as e:
            print(f"Error scraping detail page {url}: {e}")
            return {}
    
    def extract_amenities(self, soup, url):
        """Extract grouped amenities with name and image from the property's page."""
        if not self._validate_soup(soup, "extract_amenities", url):
            return {}
            
        try:
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

    def extract_builder_information_basic(self, soup, url):
        """Extract builder information from the property's page."""
        if not self._validate_soup(soup, "extract_builder_information_basic", url):
            return {}
            
        try:
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
            # Track builder error instead of printing to console
            return {}
        
    def extract_property_specification(self, soup, url):
        """Extract property specifications from the property's page."""
        try:
            spec_rows = soup.select('section#specifications table.specification-table tr')

            specifications = []

            for row in spec_rows:
                heading_tag = row.select_one('.specification-heading strong')
                value_tag = row.select_one('.specification-value span')

                if heading_tag and value_tag:
                    title = heading_tag.get_text(strip=True)
                    value = value_tag.get_text(strip=True)

                    specifications.append({
                        "title": title,
                        "value": value
                    })

            return specifications

        except Exception as e:
            print(f"Error scraping property specifications from {url}: {e}")
            return []
        
    def extract_property_about(self, soup, url):
        """Extract property about information from the property's page."""
        try:
            about_element = soup.select_one('section.about-project-section#aboutProject .content-box')

            # Extract text using a helper or directly
            about_info = about_element.decode_contents() if about_element else ""

            return about_info.strip("\n")
        except Exception as e:
            print(f"Error scraping property specifications from {url}: {e}")
            return []
        
    def extract_price_insights(self, soup, url):
        """Extract rental and comparable pricing insights from the property's page."""
        try:
            insights_section = soup.select_one('section.price-insight-section#dataPriceInsights')
            
            insights_data = {
                "rental_supply": [],
                "comparable_projects": [],
                "asking_price": []
            }
            
            # Check if insights section exists
            if not insights_section:
                return insights_data

            # === ASKING PRICE ===
            asking_price_info = insights_section.select_one('article.market-supply .price-insight-info-box')
            asking_price_data = insights_section.select_one('article.market-supply #dataPriceInsightsContainer')

            if asking_price_info or asking_price_data:
                insights_data["asking_price"] = {
                    "ininsight_info": safe_get_text(asking_price_info),
                    "data": asking_price_data.decode_contents().replace("\n", "") if asking_price_data else None,
                    "data-median": asking_price_data['data-median'] if asking_price_data and 'data-median' in asking_price_data.attrs else None,
                    "data-medianlabel": asking_price_data['data-medianlabel'] if asking_price_data and 'data-medianlabel' in asking_price_data.attrs else None,
                }

            # === RENTAL SUPPLY TABLE ===
            rental_rows = insights_section.select(
                'article.rental-supply .rental-supply-table table tbody tr'
            )
            for row in rental_rows:
                cols = row.find_all('td')
                if len(cols) == 3:
                    insights_data["rental_supply"].append({
                        "configuration": cols[0].get_text(strip=True),
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
                    insights_data["comparable_projects"].append({
                        "project": name_tag.get_text(strip=True),
                        "pricePerSqFt": price_tag.get_text(strip=True),
                    })

            return insights_data

        except Exception as e:
            print(f"Error scraping property insights from {url}: {e}")
            return {}

    def extract_nearby_landmarks(self, soup, url):
        """Extract location landmark data from the property's map section."""
        try:
            landmarks_section = soup.select_one('#mapLandmarks')
            if not landmarks_section:
                return {}

            data = {}

            # Each category is in a div.near-distance-box with attribute data-attribute="Category"
            category_blocks = landmarks_section.select('div.near-distance-box')

            for block in category_blocks:
                category_name = block.get('data-attribute', '').strip()
                entries = []

                rows = block.select('table tbody tr')
                for row in rows:
                    title_tag = row.select_one('.distance-title')
                    distance_tag = row.select_one('.distance span:last-child')

                    if title_tag and distance_tag:
                        entries.append({
                            "distance-title": title_tag.get_text(strip=True),
                            "distance": distance_tag.get_text(strip=True)
                        })

                if category_name and entries:
                    data[category_name] = entries

            return data

        except Exception as e:
            print(f"Error scraping landmarks from {url}: {e}")
            return {}

    def extract_faq(self, soup, url):
        """Extract FAQ list from the property details page."""
        try:
            faq_section = soup.select_one('#faq .faq-wrapper ul')

            if not faq_section:
                return []

            faqs = []
            for li in faq_section.find_all('li'):
                question_tag = li.find('strong')
                answer_tag = li.find('p')

                if question_tag and answer_tag:
                    faqs.append({
                        "question": question_tag.get_text(strip=True).replace("Q: ", ""),
                        "answer": answer_tag.get_text(strip=True)
                    })

            return faqs

        except Exception as e:
            print(f"Error scraping FAQ section from {url}: {e}")
            return []

    def extract_price_list(self, soup):
        """Extracts unit type, area, and price from the Price List section."""
        try:
            price_list = []

            table_rows = soup.select('#priceList table tbody tr')
            for row in table_rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    # Extract unit type + area
                    unit_info = cols[0]
                    unit_type = unit_info.find('span')
                    area = unit_info.find('strong')

                    # Extract price
                    price = cols[1].find('strong')

                    price_list.append({
                        'unit_type': (re.sub(r'\s+', ' ', unit_type.get_text(strip=True)) if unit_type else '') + " " + (area.get_text(strip=True) if area else '') or None,
                        'price': price.get_text(strip=True) if price else None
                    })

            return price_list

        except Exception as e:
            print(f"Error extracting price list: {e}")
            return []

    def extract_rera_details(self, soup):
        """Extract multiple RERA project details and Square Yards registration from the soup."""
        try:
            rera_info = []

            # Loop through each accordion item for project RERA entries
            accordion_items = soup.select('#reraDetails .accordion-item')
            for item in accordion_items:
                header = item.select_one('.accordion-header')
                rera_id = header.get('data-reraid', '').strip()

                # Extract RERA ID and project name from the <strong><span>
                strong = header.select_one('strong')
                rera_code = None
                project_name = None

                if strong:
                    strong_text = strong.get_text(strip=True)
                    rera_code = strong_text.split(' ', 1)[0]  # First part is the RERA ID
                    span = strong.select_one('span')
                    if span:
                        project_name = span.get_text(strip=True)

                rera_info.append({
                    'rera_id': rera_code or rera_id,
                    'project_name': project_name
                })

            # Get Square Yards RERA Reg.
            sq_rera_tag = soup.select_one('.qr-box .qr-content ul li b')
            sq_rera_text = sq_rera_tag.next_sibling.strip() if sq_rera_tag and sq_rera_tag.next_sibling else None

            return {
                'project_rera': rera_info,
                'square_yards_rera': sq_rera_text
            }

        except Exception as e:
            print(f"Error extracting RERA details: {e}")
            return {
                'project_rera': [],
                'square_yards_rera': None
            }

    def extract_location_description_and_insights(self, soup):
        try:
            section = soup.select_one("#localtionIntelligence")
            if not section:
                return None

            # Description
            description_tag = section.select_one(".key-insights-header .key-insights-heading .content-box")
            description = description_tag.decode_contents().replace('\n', ' ').strip() if description_tag else None

            # Insights
            insights = []
            for card in section.select(".key-insight-card"):
                img_element = card.select_one("figure img")
                icon = img_element.get('src') if img_element else None
                text = card.select_one("p").get_text(separator=" ", strip=True) if card.select_one("p") else None
                
                if icon and text:
                    icon_url = "https://www.squareyards.com/" + icon.lstrip("/") if "/assets" in icon else "https://www.squareyards.com/" + icon
                    insights.append({
                        "icon": icon_url,
                        "text": text
                    })

            # Know more URL
            know_more_tag = section.select_one(".keyinside-btn-box a")
            know_more_url = know_more_tag.get("href") if know_more_tag else None

            # extract_location_insights(know_more_url)

            return {
                "description": description,
                "insights": insights,
                "know_more_url": know_more_url
            }

        except Exception as e:
            print(f"Error in extract_location_description_and_insights: {e}")
            return None
    
    
    def extract_floor_plans(self, soup):
        try:
            # Find the main section for floor plans
            section = soup.select_one("#floorPlans")
            if not section:
                return None

            # Create a dictionary to store floor plans based on their category (3_bhk, 4_bhk, etc.)
            floor_plans = {}

            # Find all floor plan sliders (excluding "all" category)
            sliders = section.select('[id^=floorPlansSlider_]')
            
            for slider in sliders:
                # Ignore the "all" category slider
                if 'all' in slider['id']:
                    continue
                # print(f"Processing slider: {slider['id']}")
                # Extract the category from the slider ID (e.g., "floorPlansSlider_3_bhk" -> "3_bhk")
                category = slider['id'].split('floorPlansSlider_')[1] if 'floorPlansSlider_' in slider['id'] else slider['id']

                # Initialize the category in the result dictionary if not already present
                floor_plans[category] = []

                # Find all the floor plan items within this category slider
                floor_plan_items = slider.select('.floor-plan-item')

                for item in floor_plan_items:
                    # Extract the necessary details for each floor plan item
                    title = item.select_one('.floor-plan-title strong')
                    title = title.get_text(strip=True) if title else ''

                    if title:
                        match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(Sq\.?\s*Ft\.?)', title, re.IGNORECASE)
                        if match:
                            area = match.group(1).replace(',', '') +' '+  match.group(2).replace(' ', '')

                    attribute = item.select_one('.floor-plan-title span')
                    attribute = attribute.get_text(strip=True) if attribute else ''

                    img_tag = item.select_one('.unit-cover-bg img')
                    alt = img_tag['alt'] if img_tag and 'alt' in img_tag.attrs else ''
                    dd_src = img_tag['data-src'] if img_tag and 'data-src' in img_tag.attrs else ''

                    price = item.select_one('.price-box strong')
                    price = price.get_text(strip=True) if price else ''

                    # Extract the planid for the 3D virtual tour link
                    planid_tag = item.select_one('.virtual-badge')
                    planid = planid_tag['planid'] if planid_tag and 'planid' in planid_tag.attrs else ''
                    ddd_src = f"https://3dviewer-virtualtour.squareyards.com/?id={planid}" if planid else ''

                    # Add the extracted information to the floor plan list
                    floor_plans[category].append({
                        "title": title,
                        "area": area,
                        "attribute": re.sub('[()]', '', attribute),
                        "2d_src": dd_src.rpartition('?')[0] if '?' in dd_src else dd_src,
                        "alt": alt,
                        "3d_src": ddd_src,
                        "price": price
                    })

            return floor_plans

        except Exception as e:
            print(f"Error in extract_floor_plans: {e}")
            return None
    
    def extract_coordinates(self, soup, url):
        """Extract longitude and latitude coordinates from the location map section."""
        try:
            # Find the location map section
            map_section = soup.select_one('#mapLandmarks')
            if not map_section:
                return {
                    "longitude": None,
                    "latitude": None
                }

            # Look for landmark items with coordinate data
            landmark_items = map_section.select('.near-location li[data-longitude][data-latitude]')
            
            if landmark_items:
                # Get coordinates from the first landmark item (they should all be the same for the project location)
                first_item = landmark_items[0]
                longitude = first_item.get('data-longitude')
                latitude = first_item.get('data-latitude')
                
                return {
                    "longitude": float(longitude) if longitude else None,
                    "latitude": float(latitude) if latitude else None
                }
            else:
                # If no landmark items found, return None values
                return {
                    "longitude": None,
                    "latitude": None
                }

        except Exception as e:
            print(f"Error extracting coordinates from {url}: {e}")
            return {
                "longitude": None,
                "latitude": None
            } 