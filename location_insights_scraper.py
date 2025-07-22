# Location Insights Scraper for extracting sector-specific data

import requests
import time
from bs4 import BeautifulSoup
from config import HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
from utils import safe_get_text, safe_get_attribute
import re
    


def get_soup(url):
    """Get BeautifulSoup object for the given URL with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
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

def extract_location_insights(know_more_url):
    """Extract comprehensive location insights from the sector overview page."""
    if not know_more_url:
        return None
    
    try:
        soup = get_soup(know_more_url)
        if not soup:
            return None
        
        location_name = safe_get_text(soup.select_one('h1.locHeading strong'))
        Locality_info = extract_rank_price(soup)
        property_count = extract_property_counts(soup)
        
        insights_data = {
            "url": know_more_url,
            "location_name": location_name,
            "image" : safe_get_attribute(soup.select_one('.locMap img'), 'src').rpartition('?')[0] if '?' in safe_get_attribute(soup.select_one('.locMap img'), 'src') else safe_get_attribute(soup.select_one('.locMap img'), 'src'),
            "alt" : safe_get_attribute(soup.select_one('.locMap img'), 'alt'),
            "rank": Locality_info.get("rank"),
            "average_sale_price": Locality_info.get("average_sale_price"),
            "average_rental": Locality_info.get("average_rental"),
            "new_project_count": property_count.get("new_project_count"),
            "properties_for_sale_count": property_count.get("properties_for_sale_count"),
            "properties_for_rent_count": property_count.get("properties_for_rent_count"),
            "about_sector": extract_about_sector(soup),
            "indices": extract_indices(soup),
            "neighbourhood": extract_neighbourhood(soup),
            "demand_supply": extract_demand_supply(soup),
            "price_insights": extract_price_insights_for_sector(soup, know_more_url)
        }
        
        return insights_data
        
    except Exception as e:
        print(f"Error extracting location insights from {know_more_url}: {e}")
        return None

def extract_rank_price(soup):
    """Extract locality rank, average sale price, and average rental."""
    try:
       # Default values
        result = {
            "rank": {
                "position": "",
                "total_localities": "",
                "rank_text": ""
            },
            "average_sale_price": "",
            "average_rental": ""
        }

        ul = soup.select_one('.npLocalityInfo ul')
        if not ul:
            return result

        li_items = ul.find_all('li')

        for li in li_items:
            label = safe_get_text(li.find('small')).lower()
            strong_tag = li.find('strong')
            span = strong_tag.find('span') if strong_tag else None

            value_text = ""
            unit_text = ""

            # Extract text directly from strong tag (excluding nested span)
            if strong_tag:
                # Get the value part without nested span
                value_text = ''.join(strong_tag.find_all(string=True, recursive=False)).strip()
            if span:
                unit_text = span.get_text(strip=True)

            if 'rank' in label:
                position = value_text
                total_match = re.search(r'out of\s*(\d+)', safe_get_text(span))
                total = total_match.group(1) if total_match else ""

                result["rank"] = {
                    "position": position,
                    "total_localities": total,
                    "rank_text": f"{position} out of {total} localities".strip()
                }

            elif 'sale price' in label:
                result["average_sale_price"] = f"{value_text}{unit_text}".strip()

            elif 'rental' in label:
                result["average_rental"] = f"{value_text}{unit_text}".strip()

        return result


    except Exception as e:
        print(f"Error extracting rank: {e}")
        return {
            "rank": {
                "position": "",
                "total_localities": "",
                "rank_text": ""
            },
            "average_sale_price": "",
            "average_rental": ""
        }

def extract_property_counts(soup):
    """Extract count of new projects, properties for sale, and rent."""
    try:
        result = {
            "new_project_count": "",
            "properties_for_sale_count": "",
            "properties_for_rent_count": ""
        }

        ul = soup.select_one('.npPropertyInformation ul')
        if not ul:
            return result

        li_items = ul.find_all('li')
        for li in li_items:
            text = safe_get_text(li)
            number_match = re.search(r'(\d+)', text)

            if not number_match:
                continue

            count = number_match.group(1)

            if 'new project' in text.lower():
                result["new_project_count"] = count
            elif 'sale' in text.lower():
                result["properties_for_sale_count"] = count
            elif 'rent' in text.lower():
                result["properties_for_rent_count"] = count

        return result

    except Exception as e:
        print(f"Error extracting property counts: {e}")
        return {
            "new_project_count": "",
            "properties_for_sale_count": "",
            "properties_for_rent_count": ""
        }
    
def extract_about_sector(soup):
    """Extract overview HTML, what's good, and what's not good about the sector."""
    try:
        result = {
            "overview": "",
            "whats_good": [],
            "whats_not_good": []
        }

        # Extract full inner HTML under the .paraHide div (for overview)
        para_hide_div = soup.select_one('.npAbout.active .paraHide')
        if para_hide_div:
            result["overview"] = str(para_hide_div.decode_contents().replace('\n', '').strip())

        # Extract "What's Good" points
        good_list_items = soup.select('.npWhatsGood ul.thumbLike.like li span')
        result["whats_good"] = [safe_get_text(span).strip() for span in good_list_items]

        # Extract "What's Not Good" points
        not_good_list_items = soup.select('.npWhatsNotGood ul.thumbLike.dislike li span')
        result["whats_not_good"] = [safe_get_text(span).strip() for span in not_good_list_items]

        return result

    except Exception as e:
        print(f"Error extracting about sector: {e}")
        return {
            "overview": "",
            "whats_good": [],
            "whats_not_good": []
        }

def extract_indices(soup):
    """Extract indices information like Lifestyle, Livability, etc."""
    try:
        result = []

        index_boxes = soup.select(".npIndicesBox .npBox")

        for box in index_boxes:
            heading = safe_get_text(box.select_one(".npSmallHeading strong"))
            tooltip = safe_get_text(box.select_one(".npIndicesInfo .tooltip"))
            rating = safe_get_text(box.select_one(".npSmallHeading .rating"))

            # Extract bar info
            bar_div = box.select_one(".npIndicesBarPercentage")
            percentage = bar_div.get("style", "").replace("width:", "").replace("%", "").strip()
            bar_type = bar_div.get("class", [])
            bar_type = [cls for cls in bar_type if cls != "npIndicesBarPercentage"]
            bar_type = bar_type[0] if bar_type else ""

            # Extract points
            points = [safe_get_text(li) for li in box.select("ul li")]

            result.append({
                "heading": heading,
                "tooltip": tooltip,
                "rating": rating,
                "indices_bar": {
                    "percentage": percentage,
                    "type": bar_type
                },
                "points": points
            })

        return result

    except Exception as e:
        print(f"Error extracting indices: {e}")
        return []
    
def extract_neighbourhood(soup):
    """Extract neighbourhood data like schools, hotels, etc."""
    try:
        base_url = "https://www.squareyards.com"
        result = []

        cards = soup.select(".neighbourCard")

        for card in cards:
            name_raw = safe_get_text(card.select_one(".neighbourName"))
            name_match = re.match(r"(.+?)\s*\((\d+)\)", name_raw.strip())

            neighbour_name = name_match.group(1).strip() if name_match else name_raw.strip()
            count = int(name_match.group(2)) if name_match else 0

            icon_tag = card.select_one(".neighbourIcon img")
            icon_src = icon_tag.get("data-src", "").strip()
            icon_url = base_url + "/" + icon_src.lstrip("/") if icon_src else ""
            icon_alt = icon_tag.get("alt", "").strip()

            neighbour_list = [safe_get_text(span) for span in card.select("ul.neighbourList li span")]

            result.append({
                "neighbour_name": neighbour_name,
                "count": count,
                "icon": icon_url,
                "alt": icon_alt,
                "neighbourList": neighbour_list
            })

        return result

    except Exception as e:
        print(f"Error extracting neighbourhood info: {e}")
        return []
 
def extract_demand_supply(soup):
    data = {"sale": {}, "rent": {}}

    # Mapping section titles to keys
    section_map = {
        "By Property Type": "by_property_type",
        "By BHK": "by_bhk",
        "By Budget": "by_budget"
    }

    for tab in ["sale", "rent"]:
        tab_data = {}
        tab_content = soup.find("div", {"data-content": tab})
        if not tab_content:
            continue

        tables = tab_content.find_all("div", class_="demandSupplyTableBox")
        for table in tables:
            section_heading = table.find("strong", class_="demandSupplyTableHeading")
            section_key = section_map.get(section_heading.text.strip())
            if not section_key:
                continue

            rows = table.find_all("tr")
            section_data = []

            for row in rows:
                strong_tag = row.find("td", class_="type")
                if not strong_tag or not strong_tag.find("strong"):
                    continue  # Skip buttons or invalid rows

                type_name = strong_tag.find("strong").text.strip()

                demand_percent_tag = row.find("span", class_="demandPercent")
                supply_percent_tag = row.find("span", class_="supplyPercent")

                if not demand_percent_tag or not supply_percent_tag:
                    continue

                demand_percent = demand_percent_tag['style'].split(":")[1].strip().replace("%", "")
                supply_percent = supply_percent_tag['style'].split(":")[1].strip().replace("%", "")

                section_data.append({
                    "type": type_name,
                    "demand_percent": demand_percent,
                    "supplyPercent": supply_percent
                })

            tab_data[section_key] = section_data
        data[tab] = tab_data

    return data

def extract_price_insights_for_sector(soup, url):
    """Extract structured price insight data from sector insights section."""
    try:
        insights_section = soup.select_one('#dataPriceInsights')
        insights_data = {
            "asking_price": [],
            "rental_supply": [],
            "nearby_locations": [],
        }

        # === ASKING PRICE ===
        asking_price_info = insights_section.select_one('.marketSupply .npPriceInsightInfoBox')
        asking_price_data = insights_section.select_one('.marketSupply #dataPriceInsightsContainer')

        if asking_price_info or asking_price_data:
            insights_data["asking_price"] = {
                "insight_info": safe_get_text(asking_price_info),
                "data": asking_price_data.decode_contents().replace("\n", "") if asking_price_data else None,
                "data-median": asking_price_data['data-median'] if asking_price_data and 'data-median' in asking_price_data.attrs else None,
                "data-medianLabel": asking_price_data['data-medianLabel'] if asking_price_data and 'data-medianLabel' in asking_price_data.attrs else None,
            }

        # ==== RENTAL SUPPLY ====
        rental_rows = insights_section.select(
            '.npPriceInsight.rentalSupply .rentalSupplyTable table tbody tr'
        )
        for row in rental_rows:
            cols = row.find_all('td')
            if len(cols) == 2:
                insights_data["rental_supply"].append({
                    "configuration": cols[0].get_text(strip=True),
                    "inSector": cols[1].get_text(strip=True),
                })

        # === NEARBY LOCATIONS ===
        nearby_section = insights_section.select_one('.comparableProjects')
        nearby_info = nearby_section.select_one('.npPriceInsightInfoBox') if nearby_section else None
        nearby_data_items = nearby_section.select('.comparableProjectsData div') if nearby_section else []

        nearby_data = []

        for item in nearby_data_items:
            # Skip hidden items
            if 'hidden' in item.get('class', []):
                continue

            value_elem = item.select_one('.comparableProjectsValue span')
            label_elem = item.select_one('.comparableProjectsInfo')
            progress_elem = item.select_one('.diProgressBar span')

            if not (value_elem and label_elem):
                continue

            # Extract direct text from label_elem, ignoring nested tags
            label_text_node = label_elem.find(text=True, recursive=False)
            label = label_text_node.strip() if label_text_node else None
            value = value_elem.get_text(strip=True)
            progress = progress_elem.get('style', '').replace('width:', '').strip('; ') if progress_elem else None

            nearby_data.append({
                "label": label,
                "value": value,
                "progress": progress
            })

        if nearby_info or nearby_data:
            insights_data["nearby_locations"] = {
                "ininsight_info": safe_get_text(nearby_info),
                "data": nearby_data
            }



        return insights_data

    except Exception as e:
        print(f"Error extracting sector price insights from {url}: {e}")
        return {}