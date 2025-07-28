#!/usr/bin/env python3
"""
404 Error Detection Script - Enhanced tracking
"""

import sys
import os
import json
import requests
from bs4 import BeautifulSoup
sys.path.append('.')

from config import HEADERS, BASE_URL, REQUEST_TIMEOUT

def find_all_property_urls(pages):
    """Extract all property URLs from listing pages"""
    all_urls = []
    
    for page in pages:
        print(f"Scanning page {page} for property URLs...")
        url = f"{BASE_URL}{page}"
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract all property URLs
                property_links = soup.select('a.projectDetailUrl')
                for link in property_links:
                    href = link.get('href')
                    if href:
                        project_name = link.find('strong')
                        project_name = project_name.text.strip() if project_name else 'Unknown'
                        all_urls.append({
                            'name': project_name,
                            'url': href,
                            'page': page
                        })
                        
                print(f"  Found {len(property_links)} properties on page {page}")
            else:
                print(f"  Failed to fetch page {page}: Status {response.status_code}")
        except Exception as e:
            print(f"  Error scanning page {page}: {e}")
    
    return all_urls

def check_url_status(url):
    """Check if a URL returns 404 or other errors"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        return response.status_code
    except Exception as e:
        return f"Error: {e}"

def scan_for_404s():
    """Scan all property URLs for 404 errors"""
    print('🔍 Scanning for all potential 404 errors...')
    
    # Get all property URLs from pages 1-5
    all_properties = find_all_property_urls(range(1, 6))
    print(f"\n📊 Total properties found: {len(all_properties)}")
    
    # Check each URL for 404 errors
    failed_urls = []
    print(f"\n🌐 Checking URL status for all properties...")
    
    for i, prop in enumerate(all_properties, 1):
        if i % 10 == 0:
            print(f"  Checked {i}/{len(all_properties)} URLs...")
        
        status = check_url_status(prop['url'])
        if status == 404:
            failed_urls.append({
                'name': prop['name'],
                'url': prop['url'],
                'page': prop['page'],
                'status': status
            })
            print(f"  ❌ 404 Error: {prop['name']} - {prop['url']}")
        elif isinstance(status, str) and status.startswith("Error"):
            failed_urls.append({
                'name': prop['name'],
                'url': prop['url'], 
                'page': prop['page'],
                'status': status
            })
            print(f"  ⚠️ {status}: {prop['name']} - {prop['url']}")
    
    print(f"\n📋 404 Error Summary:")
    print(f"Total 404 errors found: {len([f for f in failed_urls if f['status'] == 404])}")
    print(f"Total other errors found: {len([f for f in failed_urls if f['status'] != 404])}")
    
    # Compare with existing failed items
    existing_failed = []
    if os.path.exists('output/failed_items.json'):
        with open('output/failed_items.json', 'r') as f:
            existing_failed = json.load(f)
    
    print(f"\n📊 Comparison:")
    print(f"Currently tracked failed items: {len(existing_failed)}")
    print(f"New 404 errors discovered: {len(failed_urls)}")
    
    # Show details of all 404 errors
    if failed_urls:
        print(f"\n🔍 All 404 errors found:")
        for error in failed_urls:
            print(f"  • {error['name']} (Page {error['page']}) - Status: {error['status']}")
            print(f"    URL: {error['url']}")
    
    return failed_urls

if __name__ == "__main__":
    found_404s = scan_for_404s()
    
    if found_404s:
        print(f"\n💡 Found {len(found_404s)} URLs with issues that should be tracked in failed_items.json")
    else:
        print(f"\n✅ No additional 404 errors found beyond what's already tracked")
