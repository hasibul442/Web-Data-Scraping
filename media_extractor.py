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
        figures = soup.select('.bxslider figure')  # Select all figure tags under .bxslider

        images = defaultdict(list)
        videos = []

        for fig in figures:
            try:
                sub_tab = fig.get('sub-tab')

                # Extract images
                img_tags = fig.find_all('img')
                if img_tags:
                    img = img_tags[0]
                    title = img.get('title')
                    src = img.get('src')
                    alt = img.get('alt')

                    if sub_tab and src:
                        images[sub_tab].append({
                            "title": title,
                            "src": src.split('?')[0],  # Remove any query parameters
                            "alt": alt
                        })
                    continue

                # Extract videos
                video_tags = fig.find_all('video')
                if video_tags:
                    video_tag = video_tags[0]
                    source_tags = video_tag.find_all('source')
                    if not source_tags:
                        continue
                    source = source_tags[0]
                    video_src = source.get('src')
                    video_type = source.get('type')
                    alt = video_tag.get('alt') or ""

                    videos.append({
                        "type": video_type,
                        "src": video_src,
                        "alt": alt
                    })

            except Exception as e:
                print(f"[WARN] Failed to extract one figure: {e}")
                traceback.print_exc()
                continue

        return {
            "images": dict(images),
            "videos": videos
        }

    except Exception as e:
        print(f"[ERROR] Failed to parse the response: {e}")
        return {'images': {}, 'videos': []}
