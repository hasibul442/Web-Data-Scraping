#!/usr/bin/env python3
"""
Comprehensive scan to catch all potential 404 errors
"""

import sys
import os
import json
sys.path.append('.')

from scraper import PropertyScraper

def scan_for_all_errors():
    print('🔍 Running comprehensive scan to catch all 404 errors...')
    print('Starting property scan on all pages...')
    
    scraper = PropertyScraper()
    
    # Run a complete scan of all configured pages
    results = scraper.scrape_multiple_pages(list(range(1, 6)), max_workers=5)
    
    print(f'\n📊 Scan completed!')
    print(f'Total properties found: {len(results)}')
    
    # Check for failed items
    if os.path.exists('output/failed_items.json'):
        with open('output/failed_items.json', 'r') as f:
            failed_items = json.load(f)
        print(f'Total failed items: {len(failed_items)}')
        
        # Show unique error reasons
        errors = {}
        for item in failed_items:
            reason = item.get('error_reason', 'Unknown')
            if reason not in errors:
                errors[reason] = 0
            errors[reason] += 1
        
        print('\n🔍 Error breakdown:')
        for error, count in errors.items():
            print(f'  • {error}: {count} items')
        
        # Show all failed items with details
        print(f'\n📋 All Failed Items:')
        for i, item in enumerate(failed_items, 1):
            print(f'{i}. {item.get("project_name", "Unknown")} (Page {item.get("page_number", "?")}) - {item.get("error_reason", "Unknown")}')
    else:
        print('No failed items file found.')

if __name__ == "__main__":
    scan_for_all_errors()
