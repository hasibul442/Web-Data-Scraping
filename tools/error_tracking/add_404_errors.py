#!/usr/bin/env python3
"""
Add missing 404 errors to failed items
"""

import json
import os
from datetime import datetime

def add_manual_404_errors():
    """Add any manually discovered 404 errors to the failed items list"""
    
    # Based on console output patterns, these are the typical 404 URLs we might see
    potential_404_urls = [
        "https://www.squareyards.com/gurgaon-residential-property/subh-seggovias/339597/project",
        "https://www.squareyards.com/gurgaon-residential-property/greenfield-vilasa/339605/project",
        # Add more URLs here if you find them in console output
    ]
    
    failed_items_file = "output/failed_items.json"
    
    # Load existing failed items
    existing_failed = []
    if os.path.exists(failed_items_file):
        with open(failed_items_file, 'r', encoding='utf-8') as f:
            existing_failed = json.load(f)
    
    print(f"📊 Currently tracked failed items: {len(existing_failed)}")
    
    # Check which URLs are already tracked
    existing_urls = {item.get('url') for item in existing_failed}
    
    new_items = []
    for url in potential_404_urls:
        if url not in existing_urls:
            # Extract project name and ID from URL
            parts = url.split('/')
            if len(parts) >= 6:
                project_name = parts[-3].replace('-', ' ').title()
                project_id = parts[-2]
                
                new_item = {
                    "page_number": "unknown",
                    "item_index": "unknown", 
                    "project_id": project_id,
                    "project_name": project_name,
                    "url": url,
                    "error_reason": f"Failed to fetch property page: {url}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "retry_attempts": 0,
                    "raw_item_html": ""
                }
                new_items.append(new_item)
                print(f"➕ Added new failed item: {project_name}")
            else:
                print(f"⚠️ Could not parse URL: {url}")
    
    if new_items:
        # Add new items to existing failed items
        all_failed = existing_failed + new_items
        
        # Save updated failed items
        os.makedirs(os.path.dirname(failed_items_file), exist_ok=True)
        with open(failed_items_file, 'w', encoding='utf-8') as f:
            json.dump(all_failed, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Added {len(new_items)} new failed items")
        print(f"📊 Total failed items now: {len(all_failed)}")
    else:
        print("✅ All known 404 errors are already tracked")
    
    return len(new_items)

if __name__ == "__main__":
    print("🔍 Checking for missing 404 errors to add to retry list...")
    added = add_manual_404_errors()
    
    if added > 0:
        print(f"\n💡 Run 'python check_failed_items.py' to see updated statistics")
        print(f"💡 Run 'python retry_failed_items.py' to retry all failed items")
    
    print("\n📝 If you see additional 404 errors in console output, please:")
    print("   1. Note the URL pattern")
    print("   2. Add them to the 'potential_404_urls' list in this script")
    print("   3. Run this script again to add them to the retry list")
