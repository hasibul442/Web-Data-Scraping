# Failed Items Statistics Script
# This script provides statistics about failed items

import json
import os
from collections import Counter


def analyze_failed_items():
    """Analyze and display statistics about failed items."""
    failed_items_file = "output/failed_items.json"
    
    if not os.path.exists(failed_items_file):
        print(f"No failed items file found at {failed_items_file}")
        return
    
    try:
        with open(failed_items_file, 'r', encoding='utf-8') as f:
            failed_items = json.load(f)
    except Exception as e:
        print(f"Error loading failed items: {e}")
        return
    
    if not failed_items:
        print("No failed items found")
        return
    
    print(f"📊 Failed Items Statistics")
    print("=" * 50)
    
    # Basic stats
    print(f"Total failed items: {len(failed_items)}")
    
    # Error reasons analysis
    error_reasons = [item.get('error_reason', 'Unknown') for item in failed_items]
    error_counter = Counter(error_reasons)
    
    print(f"\n🔍 Error Reasons:")
    for reason, count in error_counter.most_common():
        print(f"  • {reason}: {count} items")
    
    # Page distribution
    pages = [item.get('page_number', 'Unknown') for item in failed_items]
    page_counter = Counter(pages)
    
    print(f"\n📄 Failed Items by Page:")
    for page, count in sorted(page_counter.items()):
        print(f"  • Page {page}: {count} items")
    
    # Retry attempts analysis
    retry_counts = [item.get('retry_attempts', 0) for item in failed_items]
    retry_counter = Counter(retry_counts)
    
    print(f"\n🔄 Retry Attempts Distribution:")
    for attempts, count in sorted(retry_counter.items()):
        if attempts == 0:
            print(f"  • Never retried: {count} items")
        else:
            print(f"  • Retried {attempts} time(s): {count} items")
    
    # Show some sample failed items
    print(f"\n📋 Sample Failed Items:")
    for i, item in enumerate(failed_items[:5]):
        print(f"  {i+1}. {item.get('project_name', 'Unknown')} - {item.get('error_reason', 'Unknown')}")
    
    if len(failed_items) > 5:
        print(f"  ... and {len(failed_items) - 5} more")
    
    print(f"\n💡 To retry failed items, run: python retry_failed_items.py")


if __name__ == "__main__":
    analyze_failed_items()
