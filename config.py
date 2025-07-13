# Configuration settings for the web scraper

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

BASE_URL = "https://www.squareyards.com/new-projects-in-gurgaon?page="

# Scraping settings
MAX_WORKERS = 20
REQUEST_TIMEOUT = 10
START_PAGE = 1
END_PAGE = 2  # Adjust this range as needed

# Output settings
OUTPUT_FOLDER = 'output'
OUTPUT_FILE = 'output/gurgaon_properties.json'
ENCODING = 'utf-8'
