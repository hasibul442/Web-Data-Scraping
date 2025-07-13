# Gurgaon Properties Web Scraper

A Python web scraper for extracting property listings from SquareYards.com for Gurgaon properties.

## Project Structure

```
├── main.py              # Main script to run the scraper
├── scraper.py           # Core scraping logic and PropertyScraper class
├── config.py            # Configuration settings
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
├── php_page_scraping.py # Original single-file version (backup)
└── README.md            # This file
```

## Features

- **Modular Design**: Separated into logical components for better maintainability
- **Concurrent Scraping**: Uses ThreadPoolExecutor for faster data extraction
- **Error Handling**: Robust error handling for network issues and parsing errors
- **Safe Data Extraction**: Utility functions to safely extract data from HTML elements
- **Configurable**: Easy to modify settings through config.py

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start
```bash
python main.py
```

### Customization

Edit `config.py` to modify:
- Number of pages to scrape (START_PAGE, END_PAGE)
- Number of concurrent workers (MAX_WORKERS)
- Output filename (OUTPUT_FILE)
- Request headers and timeout settings

### Using the Scraper Class Directly

```python
from scraper import PropertyScraper
from utils import save_to_json

# Initialize scraper
scraper = PropertyScraper()

# Scrape specific pages
pages = [1, 2, 3]
results = scraper.scrape_multiple_pages(pages, max_workers=5)

# Save results
save_to_json(results, 'my_properties.json')
```

## Output Format

The scraper extracts the following data for each property:

```json
{
  "propertyId": "12345",
  "project_name": "Example Project",
  "url": "/project-url",
  "location": "Sector 1, Gurgaon",
  "developer": "Developer Name",
  "priceRange": "₹50 Lac - 1.2 Cr",
  "status": "Under Construction",
  "units": [
    {
      "unit": "2 BHK",
      "size": "1200 sq ft",
      "price": "₹75 Lac"
    }
  ]
}
```

## Error Handling

The scraper includes comprehensive error handling:
- Network timeouts and connection errors
- Missing or malformed HTML elements
- Page loading failures
- JSON serialization errors

## Notes

- The scraper respects rate limits and includes appropriate delays
- All data extraction uses safe methods to handle missing elements
- Results are saved with UTF-8 encoding to support special characters
