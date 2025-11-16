# Configuration settings for the web scraper

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

BASE_URL = "https://www.squareyards.com/search?propertyTypeId=2&cityid=1&page="

# Scraping settings
MAX_WORKERS = 10
REQUEST_TIMEOUT = 60  # Reduced from 60 to 30 seconds
MAX_RETRIES = 3       # Number of retries for failed requests
RETRY_DELAY = 2       # Delay between retries in seconds
START_PAGE = 1
END_PAGE = 1           # Adjust this range as needed

# Output settings
OUTPUT_FOLDER = 'output'
OUTPUT_FILE = 'output/gurgaon_properties.json'
ENCODING = 'utf-8'
