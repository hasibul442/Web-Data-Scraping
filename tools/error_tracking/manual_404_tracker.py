#!/usr/bin/env python3
"""
Manual 404 Error Tracker
Use this script to manually add 404 errors you see in console output
"""

import json
import os
from datetime import datetime
import re

def extract_404_from_console_log():
    """
    Extract 404 URLs from console output patterns
    
    This function helps identify 404 URLs from console patterns like:
    [ERROR] Failed to fetch page: https://www.squareyards.com/gurgaon-residential-property/project-name/123456/project | Status Code: 404 | Attempt 1/3
    """
    
    print("🔍 404 Error URL Extractor")
    print("=" * 50)
    print("If you see 404 errors in console output, please:")
    print("1. Copy the error line(s) that contain 'Status Code: 404'")
    print("2. Paste them below (one per line)")
    print("3. Press Enter twice when done")
    print()
    
    console_lines = []
    print("Paste console error lines here:")
    
    while True:
        try:
            line = input()
            if not line.strip():
                break
            console_lines.append(line.strip())
        except KeyboardInterrupt:
            break
    
    if not console_lines:
        print("No console lines provided.")
        return []
    
    # Extract URLs with 404 errors
    url_pattern = r'https://www\.squareyards\.com/gurgaon-residential-property/[^|]+/project'
    found_urls = []
    
    for line in console_lines:
        if '404' in line:
            urls = re.findall(url_pattern, line)
            found_urls.extend(urls)
    
    return found_urls

def add_urls_to_failed_items(urls):
    """Add URLs to failed items list"""
    if not urls:
        print("No URLs to add.")
        return
    
    failed_items_file = "output/failed_items.json"
    
    # Load existing failed items
    existing_failed = []
    if os.path.exists(failed_items_file):
        with open(failed_items_file, 'r', encoding='utf-8') as f:
            existing_failed = json.load(f)
    
    existing_urls = {item.get('url') for item in existing_failed}
    
    new_items = []
    for url in urls:
        if url not in existing_urls:
            # Extract project name and ID from URL
            parts = url.split('/')
            if len(parts) >= 6:
                project_name_slug = parts[-3]
                project_name = project_name_slug.replace('-', ' ').title()
                project_id = parts[-2]
                
                new_item = {
                    "page_number": "console",
                    "item_index": "manual",
                    "project_id": project_id,
                    "project_name": project_name,
                    "url": url,
                    "error_reason": f"Failed to fetch property page: {url}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "retry_attempts": 0,
                    "raw_item_html": "manually_added_from_console"
                }
                new_items.append(new_item)
                print(f"➕ Will add: {project_name} ({project_id})")
        else:
            print(f"⚠️ Already tracked: {url}")
    
    if new_items:
        # Add new items to existing failed items
        all_failed = existing_failed + new_items
        
        # Save updated failed items
        os.makedirs(os.path.dirname(failed_items_file), exist_ok=True)
        with open(failed_items_file, 'w', encoding='utf-8') as f:
            json.dump(all_failed, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Added {len(new_items)} new failed items to retry list")
        print(f"📊 Total failed items now: {len(all_failed)}")
        
        return len(new_items)
    else:
        print("No new items to add.")
        return 0

def quick_add_known_404s():
    """Quick function to add commonly known 404 errors"""
    
    # Add any URLs you've seen in console output here
    known_404_urls = [
        # Example format:
        # "https://www.squareyards.com/gurgaon-residential-property/project-name/123456/project",
    ]
    
    if not known_404_urls:
        print("No predefined 404 URLs to add.")
        return 0
    
    return add_urls_to_failed_items(known_404_urls)

def main():
    print("🔧 Manual 404 Error Tracker")
    print("=" * 40)
    print("Choose an option:")
    print("1. Extract URLs from console output (interactive)")
    print("2. Add predefined 404 URLs")
    print("3. Exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            urls = extract_404_from_console_log()
            if urls:
                print(f"\n🔍 Found URLs:")
                for url in urls:
                    print(f"  • {url}")
                
                confirm = input(f"\nAdd these {len(urls)} URLs to failed items? (y/n): ").strip().lower()
                if confirm == 'y':
                    added = add_urls_to_failed_items(urls)
                    if added > 0:
                        print(f"\n💡 Run 'python check_failed_items.py' to see updated statistics")
                        print(f"💡 Run 'python retry_failed_items.py' to retry all failed items")
                else:
                    print("Operation cancelled.")
            else:
                print("No 404 URLs found in the provided console output.")
        
        elif choice == "2":
            added = quick_add_known_404s()
            if added > 0:
                print(f"\n💡 Run 'python check_failed_items.py' to see updated statistics")
                print(f"💡 Run 'python retry_failed_items.py' to retry all failed items")
        
        elif choice == "3":
            print("Exiting...")
        
        else:
            print("Invalid choice.")
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")

if __name__ == "__main__":
    main()
