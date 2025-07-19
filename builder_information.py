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

    soup = get_soup(builder_page_url)
    if not soup:
        return {}

    # data = get_head_office_address(soup)
    # print(f"[INFO] Extracted head office address: {data}")
    # exit()
    
    return {
        "overview": get_builder_description(soup),
        "head_office_address": get_head_office_address(soup),
        "branch_office_address": get_branch_offices(soup),
        "company_size": get_company_size(soup),
        "management_team": get_management_team(soup),
        "key_service_and_specialities": get_key_service_and_specialities(soup),
        "awards_and_recognition": get_awards_and_recognition(soup),
        "customer_care_number" : get_customer_care_number(soup),
        "faq": extract_faq_data(soup),
        "projects_in_top_cities": extract_operating_cities(soup),
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
    
def get_branch_offices(soup):
    """Extract branch office addresses by city."""
    branch_offices = []

    # Select all office address containers within branchOfficeBox
    office_tags = soup.select('.branchOfficeBox .branchOfficeBody .mainOfficeAddress')

    for office in office_tags:
        city = office.get('data-name') or office.select_one('span') and office.select_one('span').get_text(strip=True)
        lat = office.get('data-lat')
        long = office.get('data-long')
        address_tag = office.select_one('.mainOfficeLocation span p')
        address = address_tag.get_text(strip=True) if address_tag else None

        branch_offices.append({
            'city': city,
            'latitude': lat,
            'longitude': long,
            'address': address
        })

    return branch_offices

def get_company_size(soup):
    """Extract company size and its description."""
    section = soup.select_one('#companySize')
    if not section:
        return None

    size_tag = section.select_one('.companySizeBody .sizeOfCompany span')
    size = size_tag.get_text(strip=True) if size_tag else None

    description_tags = section.select('.companySizeBody p span')
    description = ' '.join([tag.get_text(strip=True) for tag in description_tags if tag.get_text(strip=True)])

    return {
        'company_size': size,
        'description': description
    }

def get_management_team(soup):
    """Extract management team details grouped by position."""
    section = soup.select_one('#managementTeam')
    if not section:
        return {}

    team_data = {}

    # ===== CEO / Executive Team =====
    ceo_heading = section.select_one('.ownersHeading span')
    ceo_title = ceo_heading.get_text(strip=True) if ceo_heading else "CEO"

    team_data[ceo_title] = []
    for profile in section.select('.ownersProfileBox'):
        img_tag = profile.select_one('.profileImg img')
        name_tag = profile.select_one('.profileDetail strong')
        desc_tag = profile.select_one('.profileDetail span')

        image = img_tag.get('data-src')
        name = name_tag.get_text(strip=True) if name_tag else None
        description = desc_tag.get_text(strip=True) if desc_tag else None

        team_data[ceo_title].append({
            'name': name,
            'image': image,
            'description': description
        })

    # ===== Owners / Team Carousel =====
    owners_heading = section.select_one('.companyOwnersBox .ownersHeading span')
    owners_title = owners_heading.get_text(strip=True) if owners_heading else "Owners / Team"

    team_data[owners_title] = []
    for card in section.select('.ourTeamCard'):
        img_tag = card.select_one('figure img')
        name_tag = card.select_one('.profileName')
        role_tag = card.select_one('.designationName span')

        image = img_tag.get('data-src')
        name = name_tag.get_text(strip=True) if name_tag else None
        description = role_tag.get_text(strip=True) if role_tag else None

        team_data[owners_title].append({
            'name': name,
            'image': image,
            'description': description
        })

    return team_data

def get_key_service_and_specialities(soup):
    """Extract the full inner HTML of the .descriptionBox section under #keyServices."""
    box = soup.select_one('#keyServices .descriptionBox')
    if not box:
        return None
    return str(box)

def get_awards_and_recognition(soup):
    """Extract the full inner HTML of the .descriptionBox section under #keyServices."""
    box = soup.select_one('div#awards .awardDescription')
    if not box:
        return None
    return str(box)

def get_customer_care_number(soup):
    """Extract the customer care number from the contact section."""
    tag = soup.select_one('div#contact .descriptionBox .telephoneNumber a')
    if tag:
        return tag.get_text(strip=True)
    return None

def extract_faq_data(soup):
    faqs = []
    panels = soup.select('#faq .accordianBox .panel')
    for panel in panels:
        question_tag = panel.select_one('.panelHeader strong')
        answer_tag = panel.select_one('.panelBody p span')
        question = question_tag.get_text(strip=True) if question_tag else None
        answer = answer_tag.get_text(strip=True) if answer_tag else None
        if question and answer:
            faqs.append({
                "question": question,
                "answer": answer
            })
    return faqs

def extract_operating_cities(soup):
    city_links = []
    chip_boxes = soup.select('#operatingCities .chipFlexBox .chipFlex a.chipBox')
    for chip in chip_boxes:
        city_name = chip.get_text(strip=True)
        city_url = chip.get('href')
        city_links.append({
            'city': city_name,
            'url': city_url
        })
    return city_links
