# Utility functions for the web scraper

import json
import os

def save_to_json(data, filename, encoding='utf-8'):
    """Save data to a JSON file with proper encoding."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False

def flatten_list_of_lists(list_of_lists):
    """Flatten a list of lists into a single list."""
    result = []
    for sublist in list_of_lists:
        if isinstance(sublist, list):
            result.extend(sublist)
        else:
            result.append(sublist)
    return result

def safe_get_text(element, default=''):
    """Safely get text from a BeautifulSoup element."""
    if element:
        return element.get_text(strip=True)
    return default

def safe_get_attribute(element, attribute, default=''):
    """Safely get an attribute from a BeautifulSoup element."""
    if element:
        return element.get(attribute, default)
    return default
