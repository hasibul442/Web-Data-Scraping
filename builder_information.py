import requests
from bs4 import BeautifulSoup

# Set headers and timeout globally (or customize as needed)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}
TIMEOUT = 10

def get_soup(url):
    """Fetch and parse the HTML content from a URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch page: {url} | Status Code: {response.status_code}")
            return None
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"[EXCEPTION] While fetching {url}: {e}")
        return None

def extract_builder_information(soupbody, url):
    heading_tag = soupbody.select_one('section.about-builder-section#aboutBuilder h2')
    if not heading_tag:
        print(f"[ERROR] Failed to find builder information section in {url}")
        return {}

    link_tag = heading_tag.find('a')
    if not link_tag or not link_tag.get('href'):
        print(f"[ERROR] Builder link not found in h2 tag on {url}")
        return {}

    builder_page_url = link_tag['href']
    print(f"[INFO] Fetching builder information from {builder_page_url}")

    soup = get_soup(builder_page_url)
    if not soup:
        return {}

    # data = get_head_office_address(soup)
    # print(f"[INFO] Extracted head office address: {data}")
    # exit()
    return {
        "overview": get_builder_description(soup),
        "head_office_address": get_head_office_address(soup),
        "city_or_country_office_address": "",
        "company_size": "",
        "management_team": "",
        "key_service_and_specialities": "",
        "awards_and_recognition": "",
        "customer_care_number" : "",
        "faq": [],
        "projects_in_top_cities": [],
    }

def get_builder_description(soup):
    """Extract builder description from the soup body."""
    description_tag = soup.select_one('div.description#overview .descriptionBox')
    description = description_tag.get_text(strip=True) if description_tag else "No description available"
    return description
    
def get_head_office_address(soup):
    """Extract builder head office details from the soup."""
    try:
        address_box = soup.select_one('.mainOfficeBox .mainOfficeAddress')
        if not address_box:
            return {}

        # Extract values
        title = address_box.select_one('strong')
        city = address_box.select_one('span')
        location = address_box.select_one('.mainOfficeLocation span')

        return {
            "title": title.get_text(strip=True) if title else None,
            "city": city.get_text(strip=True) if city else None,
            "location": location.get_text(strip=True) if location else None,
            "latitude": address_box.get("data-lat"),
            "longitude": address_box.get("data-long"),
        }

    except Exception as e:
        print(f"Error extracting head office address: {e}")
        return {}
    
   