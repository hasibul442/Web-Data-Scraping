# Web scraper for Gurgaon properties

import time
import traceback
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from config import HEADERS, BASE_URL, REQUEST_TIMEOUT
from utils import safe_get_text, safe_get_attribute
import re
# import undetected_chromedriver as uc
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from collections import defaultdict
from tqdm import tqdm

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
            for item in tqdm(listings[0:3]):
                try:
                    property_data = self._extract_property_data(item)
                    if property_data:
                        page_data.append(property_data)
                except Exception as e:
                    print(f"Error parsing one property on page {page}: {e}")
                    traceback.print_exc()
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
        # units = self._extract_units(item)

        soup = self.get_soup(url)  # Call only once per page
        project_spec = self.extract_project_specifications(soup, url)
        amenities = self.extract_amenities(soup, url)
        builder_info = self.extract_builder_information(soup, url)
        property_spec = self.extract_property_specification(soup, url)
        property_about = self.extract_property_about(soup, url)
        price_insights = self.extract_price_insights(soup, url)
        nearby_landmarks = self.extract_nearby_landmarks(soup, url)
        faq = self.extract_faq(soup, url)
        price_list = self.extract_price_list(soup)
        rera = self.extract_rera_details(soup)
        location_insights = self.extract_location_description_and_insights(soup)
        all_media = self.extract_media_by_sub_tab(url)

        return {
            'property_id': project_id,
            'project': {
                'name': project_name,
                'location': location,
                'status': status,
                'price': price_range,
                'about': property_about,
                "information": property_spec,
                'specifications': project_spec,
                'amenities': amenities,
                'nearby_landmarks': nearby_landmarks,
                'price_insights': price_insights,
                'price_list': price_list,
                'rera': rera,
                'location_insights': location_insights,
            },
            'builder_info': builder_info,
            'faq': faq,
            'image': "https://static.squareyards.com/" + image if image else None,
            'all_media': all_media,
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


    def get_soup(self, url):
        """Reusable method to perform GET request and return parsed HTML soup."""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                print(f"[ERROR] Failed to fetch page: {url} | Status Code: {response.status_code}")
                return None
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"[EXCEPTION] While fetching {url}: {e}")
            return None
        
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

    def extract_project_specifications(self, soup, url):
        """Scrape the details from a property's individual page."""
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

    def extract_builder_information(self, soup, url):
        """Extract builder information from the property's page."""
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
            print(f"Error scraping builder information from {url}: {e}")
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

            return about_info

        except Exception as e:
            print(f"Error scraping property specifications from {url}: {e}")
            return []
        
    def extract_price_insights(self, soup, url):
        """Extract rental and comparable pricing insights from the property's page."""
        try:
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
            description = description_tag.decode_contents() if description_tag else None
  
            # Insights
            insights = []
            for card in section.select(".key-insight-card"):
                icon = card.select_one("figure img")['src'] if card.select_one("figure img") else None
                text = card.select_one("p").get_text(separator=" ", strip=True) if card.select_one("p") else None
                insights.append({
                    "icon": "https://www.squareyards.com/" + icon.lstrip("/") if "/assets" in icon else "https://www.squareyards.com/" + icon,
                    "text": text
                })

            # Know more URL
            know_more_tag = section.select_one(".keyinside-btn-box a")
            know_more_url = know_more_tag.get("href") if know_more_tag else None

            return {
                "description": description,
                "insights": insights,
                "know_more_url": know_more_url
            }

        except Exception as e:
            print(f"Error in extract_location_description_and_insights: {e}")
            return None

    def extract_media_by_sub_tab(self, url):

        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5; rv:130.0) Gecko/20100101 Firefox/130.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Edg/128.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Edg/128.0.0.0",
            "Mozilla/5.0 (Android 14; Mobile; rv:130.0) Gecko/130.0 Firefox/130.0"
        ]

        user_agent = random.choice(USER_AGENTS)


        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--start-maximized")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # load page
        driver.get(url)
        time.sleep(random.uniform(2, 4))

        try:
            wait = WebDriverWait(driver, 15)

            # Open gallery modal
            try:
                trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.load-gallery')))
                trigger.click()
                time.sleep(2)  # wait for animation
            except TimeoutException:
                print(f"[TIMEOUT] Could not click '.load-gallery' on {url}")
                driver.save_screenshot("timeout_error.png")
                return {'images': {}, 'videos': []}

            # Wait for gallery content
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.bxslider figure')))
            figures = driver.find_elements(By.CSS_SELECTOR, '.bxslider figure')

            images = defaultdict(list)
            videos = []

            for fig in figures:
                try:
                    sub_tab = fig.get_attribute("sub-tab")

                    # --- Image ---
                    img_tags = fig.find_elements(By.TAG_NAME, 'img')
                    if img_tags:
                        img = img_tags[0]
                        title = img.get_attribute("title")
                        src = img.get_attribute("src")
                        alt = img.get_attribute("alt")

                        if sub_tab and src:
                            images[sub_tab].append({
                                "title": title,
                                "src": src.split('?')[0],
                                "alt": alt
                            })
                        continue

                    # --- Video ---
                    video_tags = fig.find_elements(By.TAG_NAME, 'video')
                    if video_tags:
                        video_tag = video_tags[0]
                        source_tags = video_tag.find_elements(By.TAG_NAME, 'source')
                        if not source_tags:
                            continue
                        source = source_tags[0]
                        video_src = source.get_attribute("src")
                        video_type = source.get_attribute("type")
                        alt = video_tag.get_attribute("alt") or ""

                        videos.append({
                            "type": video_type,
                            "src": video_src,
                            "alt": alt
                        })

                except Exception as e:
                    print(f"[WARN] Failed to extract one figure: {e}")
                    traceback.print_exc()
                    continue

            # Final structured result
            return {
                "images": dict(images),
                "videos": videos
            }

        finally:
            driver.quit()




# for 3d use this link https://3dviewer-virtualtour.squareyards.com/?id=478940