import requests
from bs4 import BeautifulSoup
import time

# Import configuration from config.py
from core.config import HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY

def get_soup(url):
    """Fetch and parse the HTML content from a URL with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            # Suppress error output - errors will be tracked by the main scraper
        except (requests.RequestException, requests.ConnectTimeout, requests.ReadTimeout) as e:
            # Suppress error output - errors will be tracked by the main scraper
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            # Suppress error output - errors will be tracked by the main scraper
            break
            
    # Return None without printing - error will be tracked by main scraper
    return None

def extract_builder_information(soupbody, url):
    # Check if soup is None first
    if soupbody is None:
        return {"error": f"No soup provided for builder information extraction from {url}"}
        
    heading_tag = soupbody.select_one('section.about-builder-section#aboutBuilder strong')

    if not heading_tag:
        return {"error": f"Failed to find builder information section in {url}"}

    link_tag = heading_tag.find('a')
    if not link_tag or not link_tag.get('href'):
        return {"error": f"Builder link not found in h2 tag on {url}"}

    builder_page_url = link_tag['href']
    soup = get_soup(builder_page_url)
    if not soup:
        return {"error": f"Failed to fetch builder page: {builder_page_url}"}

    
    return {
        "id" : builder_page_url.split('/')[-2],
        "name": get_builder_short_description(soup).get("name", ""),
        "image": get_builder_short_description(soup).get("image", {}),
        "experience": get_builder_short_description(soup).get("experience", ""),
        "projects": get_builder_short_description(soup).get("projects", {}),
        "overview": get_builder_description(soup),
        "head_office_address": get_head_office_address(soup),
        "branch_office_address": get_branch_offices(soup),
        "company_size": get_company_size(soup),
        "management_team": get_management_team(soup),
        "key_service_and_specialities": get_key_service_and_specialities(soup).replace('\n', ' ').strip() if get_key_service_and_specialities(soup) else None,
        "awards_and_recognition": get_awards_and_recognition(soup).replace('\n', ' ').strip() if get_awards_and_recognition(soup) else None,
        "customer_care_number" : get_customer_care_number(soup),
        "faq": extract_faq_data(soup),
        "projects_in_top_cities": extract_operating_cities(soup),
    }

def get_builder_short_description(soup):
    """Extract builder short description from the soup body."""
    if not soup:
        return {"image": {}, "experience": "", "projects": {}, "name": ""}
        
    image_tag = soup.select_one('.builderLogo img')
    name = soup.select_one('.builderLogoBox h1.builderName')
    experience_tag = soup.select_one('.builderSortDetail .totalExperience')
    projects_tag = soup.select_one('.builderSortDetail .totalProject')

    # Default counts
    ongoing_count = 0
    past_count = 0

    if projects_tag:
        project_items = projects_tag.select('.totalProjectLi')
        
        for item in project_items:
            label = item.select_one('span')
            count = item.select_one('strong')
            
            if label and count:
                text = label.get_text(strip=True).lower()
                num = int(count.get_text(strip=True))
                
                if 'on going' in text:
                    ongoing_count = num
                elif 'past' in text:
                    past_count = num

    total_count = ongoing_count + past_count
    
    # Handle image source safely
    image_src = ""
    image_alt = ""
    if image_tag:
        src = image_tag.get('src', '')
        if src and '?' in src:
            image_src = src.rpartition('?')[0]
        else:
            image_src = src
        image_alt = image_tag.get('alt', '')

    return {
            "image": {"src": image_src, "alt": image_alt},
            "experience": experience_tag.get_text(strip=True).replace(' Years Experience', '') if experience_tag else "",
            "name": name.get_text(strip=True) if name else "",
            "projects": {"on_going": ongoing_count, "past": past_count, "total": total_count}
        }

def get_builder_description(soup):
    """Extract builder description from the soup body."""
    if not soup:
        return "No description available"
        
    description_tag = soup.select_one('div.description#overview .descriptionBox')
    description = description_tag.get_text(strip=True) if description_tag else "No description available"
    return description
    
def get_head_office_address(soup):
    """Extract builder head office details from the soup."""
    if not soup:
        return {}
        
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
            "location": location.get_text(strip=True).replace('\r\n\r\n', ' ') if location else None,
            "latitude": address_box.get("data-lat"),
            "longitude": address_box.get("data-long"),
        }

    except Exception as e:
        # Suppress error output - errors will be tracked by the main scraper
        return {}
    
def get_branch_offices(soup):
    """Extract branch office addresses by city."""
    if not soup:
        return []
        
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
    if not soup:
        return None
        
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
    if not soup:
        return {}
        
    section = soup.select_one('#managementTeam')
    if not section:
        return {}

    team_data = {}

    # ===== CEO / Executive Team =====
    ceo_heading = section.select_one('.ownersHeading span')
    # ceo_title = ceo_heading.get_text(strip=True) if ceo_heading else "CEO"
    ceo_title = "CEO"

    team_data[ceo_title] = []
    for profile in section.select('.ownersProfileBox'):
        img_tag = profile.select_one('.profileImg img')
        name_tag = profile.select_one('.profileDetail strong')
        desc_tag = profile.select_one('.profileDetail span')

        # Handle null img_tag to prevent AttributeError
        image = img_tag.get('data-src') if img_tag else None
        name = name_tag.get_text(strip=True) if name_tag else None
        description = desc_tag.get_text(strip=True) if desc_tag else None

        team_data[ceo_title].append({
            'name': name,
            'image': image,
            'description': description
        })

    # ===== Owners / Team Carousel =====
    owners_heading = section.select_one('.companyOwnersBox .ownersHeading span')
    # owners_title = owners_heading.get_text(strip=True) if owners_heading else "Owners / Team"
    owners_title = "owners_or_team"

    team_data[owners_title] = []
    for card in section.select('.ourTeamCard'):
        img_tag = card.select_one('figure img')
        name_tag = card.select_one('.profileName')
        role_tag = card.select_one('.designationName span')

        # Handle null img_tag to prevent AttributeError
        image = img_tag.get('data-src') if img_tag else None
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
    if not soup:
        return None
        
    box = soup.select_one('#keyServices .descriptionBox')
    if not box:
        return None
    return str(box)

def get_awards_and_recognition(soup):
    """Extract the full inner HTML of the .descriptionBox section under #keyServices."""
    if not soup:
        return None
        
    box = soup.select_one('div#awards .awardDescription')
    if not box:
        return None
    return str(box)

def get_customer_care_number(soup):
    """Extract the customer care number from the contact section."""
    if not soup:
        return None
        
    tag = soup.select_one('div#contact .descriptionBox .telephoneNumber a')
    if tag:
        return tag.get_text(strip=True)
    return None

def extract_faq_data(soup):
    if not soup:
        return []
        
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
    if not soup:
        return []
        
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
