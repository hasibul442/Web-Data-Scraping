# media_extractor.py
import random
import time
import traceback
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


def extract_media_by_sub_tab(url):
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
    options.add_argument("--headless")
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    driver.get(url)
    time.sleep(random.uniform(2, 4))

    try:
        wait = WebDriverWait(driver, 15)

        try:
            trigger = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.load-gallery')))
            trigger.click()
            time.sleep(2)
        except TimeoutException:
            print(f"[TIMEOUT] Could not click '.load-gallery' on {url}")
            driver.save_screenshot("timeout_error.png")
            return {'images': {}, 'videos': []}

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.bxslider figure')))
        figures = driver.find_elements(By.CSS_SELECTOR, '.bxslider figure')

        images = defaultdict(list)
        videos = []

        for fig in figures:
            try:
                sub_tab = fig.get_attribute("sub-tab")

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

        return {
            "images": dict(images),
            "videos": videos
        }

    finally:
        driver.quit()
        print(f"[INFO] Finished extracting media from {url}")