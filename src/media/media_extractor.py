import random
import time
import traceback
import requests
from collections import defaultdict
from bs4 import BeautifulSoup

def extract_media_by_sub_tab(project_id, url):

    request_url = 'https://www.squareyards.com/loadcommongallery'
    
    # Set the payload for the POST request
    payload = {
        "projectId": project_id,
        "type": "Project"
    }

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

    # Choose a random user agent for the request
    user_agent = random.choice(USER_AGENTS)

    # Prepare headers
    headers = {
        'User-Agent': user_agent
        }

    response = requests.post(request_url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"[ERROR] Failed to fetch data from {url}. Status code: {response.status_code}")
        return {'images': {}, 'videos': []}

    # Parse the HTML response with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        images = defaultdict(list)
        videos = []

        # Find all gallery tab content sections
        gallery_sections = soup.select('.sy-gallery.gallery-tab-content')
        
        for gallery in gallery_sections:
            tab_type = gallery.get('data-tab', '')
            
            # Find all white-box sections within this gallery
            white_boxes = gallery.select('.white-box')
            
            for box in white_boxes:
                # Get the category from the heading
                heading_element = box.select_one('.white-box-heading')
                if not heading_element:
                    continue
                    
                category = heading_element.get_text(strip=True)
                
                # Handle videos section
                if category.lower() == 'videos':
                    video_links = box.select('a[href$=".mp4"]')
                    for link in video_links:
                        video_src = link.get('href')
                        title = link.get('data-title', '').strip()
                        
                        # Try to get alt text from thumbnail image
                        img = link.select_one('img')
                        alt = img.get('alt', '') if img else ''
                        
                        if video_src:
                            videos.append({
                                "type": "video/mp4",
                                "src": video_src,
                                "alt": alt,
                                "title": title
                            })
                else:
                    # Handle image sections
                    image_links = box.select('a[href]')
                    for link in image_links:
                        href = link.get('href', '')
                        
                        # Skip video links
                        if href.endswith('.mp4'):
                            continue
                            
                        # Get image details
                        img = link.select_one('img')
                        if not img:
                            continue
                            
                        # Get image URL from href (full size) or data-src (thumbnail)
                        img_src = href if href.startswith('http') else img.get('data-src') or img.get('src')
                        if not img_src:
                            continue
                            
                        title = link.get('data-title', '').strip()
                        alt = img.get('alt', '').strip()
                        
                        # Clean up title - extract just the text part
                        if title:
                            # Remove HTML tags from title
                            title_soup = BeautifulSoup(title, 'html.parser')
                            title = title_soup.get_text(strip=True)
                        
                        # Determine the category key based on tab and section
                        if tab_type.lower() == 'units':
                            # For units tab, use the section heading (like "4 BHK", "5 BHK")
                            category_key = f"floor_plans_{category.lower().replace(' ', '_')}"
                        else:
                            # For project tab, use the section heading
                            category_key = category.lower().replace(' ', '_').replace('-', '_')
                        
                        images[category_key].append({
                            "title": title,
                            "src": img_src.split('?')[0],  # Remove query parameters
                            "alt": alt
                        })

        return {
            "images": dict(images),
            "videos": videos
        }

    except Exception as e:
        print(f"[ERROR] Failed to parse the response: {e}")
        traceback.print_exc()
        return {'images': {}, 'videos': []}
