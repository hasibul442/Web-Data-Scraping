

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import json

HEADERS = {'User-Agent': 'Mozilla/5.0'}
BASE_URL = "https://www.squareyards.com/new-projects-in-gurgaon?page="

results = []

def scrape_page(page):
    try:
        print(f"Scraping page {page}")
        res = requests.get(BASE_URL + str(page), headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        listings = soup.find_all('div', class_='npTile')

        page_data = []
        for item in listings:
            try:
                fav_btn = item.select_one('.npFavBtn')
                project_id = fav_btn.get('data-projectid')
                project_name = item.select_one('.npProjectName a strong').get_text(strip=True)
                url = item.select_one('.npProjectName a').get('href')
                location = item.select_one('.npProjectCity').get_text(strip=True)
                developer = item.select_one('.npDeveloperLogo img').get('alt', '')
                price_range = item.select_one('.npPriceBox').get_text(strip=True)
                # description = item.select_one('.npDescBox').get_text(strip=True) if fav_btn else ''
                status = fav_btn.get('data-propstatus') if fav_btn else ''
                # rera = bool(item.select_one('.npPropertyTagList .rera'))

                # Image
                # image_url = item.select_one('.npTileFigure img')
                # image = image_url.get('src').split('?')[0] if image_url else ''

                # Units
                unit_rows = item.select('.pTable tbody tr')
                units = []
                for row in unit_rows:
                    cols = row.find_all('td')
                    if len(cols) == 3:
                        units.append({
                            'unit': cols[0].get_text(strip=True),
                            'size': cols[1].get_text(strip=True),
                            'price': cols[2].get_text(strip=True)
                        })

                page_data.append({
                    'propertyId': project_id,
                    'project_name': project_name,
                    'url': url,
                    'location': location,
                    'developer': developer,
                    'priceRange': price_range,
                    'status': status,
                    # 'reraRegistered': rera,
                    # 'description': description,
                    'units': units
                    # 'image': image
                })
            except Exception as e:
                print(f"{project_id}-Error parsing one project: {e}")

                continue
        return page_data
    except Exception as e:
        print(f"Error scraping page {page}: {e}")
        return []

# Run in parallel
with ThreadPoolExecutor(max_workers=20) as executor:
    pages = list(range(1, 2))  # adjust range
    all_pages_data = list(executor.map(scrape_page, pages))

# Flatten list
for page_data in all_pages_data:
    results.extend(page_data)

# Save as JSON
with open('gurgaon_properties_fast.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Scraped {len(results)} listings.")

"""Back Up Code"""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import json

HEADERS = {'User-Agent': 'Mozilla/5.0'}
BASE_URL = "https://www.squareyards.com/new-projects-in-gurgaon?page="

results = []

def scrape_page(page):
    try:
        print(f"Scraping page {page}")
        res = requests.get(BASE_URL + str(page), headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        listings = soup.find_all('div', class_='npTile')

        page_data = []
        for item in listings:
            try:
                fav_btn = item.select_one('.npFavBtn')
                project_id = fav_btn.get('data-projectid')
                project_name = item.select_one('.npProjectName a strong').get_text(strip=True)
                url = item.select_one('.npProjectName a').get('href')
                location = item.select_one('.npProjectCity').get_text(strip=True)
                developer = item.select_one('.npDeveloperLogo img').get('alt', '')
                price_range = item.select_one('.npPriceBox').get_text(strip=True)
                description = item.select_one('.npDescBox').get_text(strip=True)
                status = fav_btn.get('data-propstatus') if fav_btn else ''
                rera = bool(item.select_one('.npPropertyTagList .rera'))

                # Image
                # image_url = item.select_one('.npTileFigure img')
                # image = image_url.get('src').split('?')[0] if image_url else ''

                # Units
                unit_rows = item.select('.pTable tbody tr')
                units = []
                for row in unit_rows:
                    cols = row.find_all('td')
                    if len(cols) == 3:
                        units.append({
                            'unit': cols[0].get_text(strip=True),
                            'size': cols[1].get_text(strip=True),
                            'price': cols[2].get_text(strip=True)
                        })

                page_data.append({
                    'propertyId': project_id,
                    'project_name': project_name,
                    'url': url,
                    'location': location,
                    'developer': developer,
                    'priceRange': price_range,
                    'status': status,
                    'reraRegistered': rera,
                    'description': description,
                    'units': units
                    # 'image': image
                })
            except Exception as e:
                print(f"Error parsing one project: {e}")
                continue
        return page_data
    except Exception as e:
        print(f"Error scraping page {page}: {e}")
        return []

# Run in parallel
with ThreadPoolExecutor(max_workers=20) as executor:
    pages = list(range(1, 2))  # adjust range
    all_pages_data = list(executor.map(scrape_page, pages))

# Flatten list
for page_data in all_pages_data:
    results.extend(page_data)

# Save as JSON
with open('gurgaon_properties_fast.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Scraped {len(results)} listings.")