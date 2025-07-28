# Retry Failed Items Script
# This script reads failed items from failed_items.json and retries scraping them

import json
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from scraper import PropertyScraper
from config import OUTPUT_FILE
import traceback


class FailedItemsRetry:
    """Class to handle retrying failed property items."""
    
    def __init__(self):
        self.failed_items_file = "output/failed_items.json"
        self.main_output_file = OUTPUT_FILE
        self.retry_log_file = "output/retry_log.txt"
        self.scraper = PropertyScraper()
    
    def load_failed_items(self):
        """Load failed items from JSON file."""
        if not os.path.exists(self.failed_items_file):
            print(f"No failed items file found at {self.failed_items_file}")
            return []
        
        try:
            with open(self.failed_items_file, 'r', encoding='utf-8') as f:
                failed_items = json.load(f)
            print(f"Loaded {len(failed_items)} failed items for retry")
            return failed_items
        except Exception as e:
            print(f"Error loading failed items: {e}")
            return []
    
    def load_main_data(self):
        """Load main scraped data."""
        if not os.path.exists(self.main_output_file):
            print(f"Main output file not found at {self.main_output_file}")
            return {"projects": [], "builders": [], "locations": []}
        
        try:
            with open(self.main_output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded main data with {len(data.get('projects', []))} projects")
            return data
        except Exception as e:
            print(f"Error loading main data: {e}")
            return {"projects": [], "builders": [], "locations": []}
    
    def retry_failed_item(self, failed_item):
        """Retry scraping a single failed item."""
        try:
            print(f"Retrying: {failed_item.get('project_name', 'Unknown')} from {failed_item.get('url', 'Unknown URL')}")
            
            # Parse the raw HTML
            item_soup = BeautifulSoup(failed_item['raw_item_html'], 'html.parser')
            
            # Use the scraper's extraction method
            property_data = self.scraper._extract_property_data(item_soup)
            
            if property_data:
                print(f"✅ Successfully retried: {property_data.get('name', 'Unknown')}")
                return property_data, True
            else:
                print(f"❌ Failed to extract data during retry: {failed_item.get('project_name', 'Unknown')}")
                return None, False
                
        except Exception as e:
            print(f"❌ Exception during retry for {failed_item.get('project_name', 'Unknown')}: {e}")
            traceback.print_exc()
            return None, False
    
    def update_main_data_with_retry(self, main_data, successful_retries):
        """Update main data by replacing failed items with successful retries."""
        if not successful_retries:
            print("No successful retries to merge")
            return main_data
        
        # Create a mapping of project_id to successful retry data
        retry_map = {item['property_id']: item for item in successful_retries}
        
        # Track replacements
        replacements_made = 0
        
        # Replace or add successful retries in projects
        for i, project in enumerate(main_data.get('projects', [])):
            project_id = project.get('property_id')
            if project_id in retry_map:
                print(f"Replacing project {project.get('name', 'Unknown')} with retry data")
                main_data['projects'][i] = retry_map[project_id]
                replacements_made += 1
                del retry_map[project_id]  # Remove from map after processing
        
        # Add any remaining successful retries as new projects
        for project_id, project_data in retry_map.items():
            print(f"Adding new project from retry: {project_data.get('name', 'Unknown')}")
            main_data['projects'].append(project_data)
            replacements_made += 1
        
        # Update builders and locations collections from successful retries
        for retry_item in successful_retries:
            # Add builder if not exists
            if retry_item.get('builder_info'):
                builder_id = retry_item['builder_info'].get('builder_id')
                if builder_id and not any(b.get('id') == builder_id for b in main_data.get('builders', [])):
                    # Get full builder data from scraper's collection
                    if builder_id in self.scraper.builders_collection:
                        main_data.setdefault('builders', []).append(self.scraper.builders_collection[builder_id])
            
            # Add location if not exists
            if retry_item.get('location_insights'):
                location_id = retry_item['location_insights'].get('location_id')
                if location_id and not any(l.get('id') == location_id for l in main_data.get('locations', [])):
                    # Get full location data from scraper's collection
                    if location_id in self.scraper.location_insights_collection:
                        main_data.setdefault('locations', []).append(self.scraper.location_insights_collection[location_id])
        
        print(f"Made {replacements_made} replacements/additions to main data")
        return main_data
    
    def remove_successful_from_failed(self, failed_items, successful_project_ids):
        """Remove successfully retried items from failed items list."""
        remaining_failed = []
        for item in failed_items:
            if item.get('project_id') not in successful_project_ids:
                remaining_failed.append(item)
        
        print(f"Removed {len(failed_items) - len(remaining_failed)} successful items from failed list")
        return remaining_failed
    
    def save_data(self, main_data, remaining_failed_items):
        """Save updated main data and remaining failed items."""
        # Save updated main data
        try:
            with open(self.main_output_file, 'w', encoding='utf-8') as f:
                json.dump(main_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Updated main data saved to {self.main_output_file}")
        except Exception as e:
            print(f"❌ Error saving main data: {e}")
        
        # Save remaining failed items
        try:
            with open(self.failed_items_file, 'w', encoding='utf-8') as f:
                json.dump(remaining_failed_items, f, indent=2, ensure_ascii=False)
            print(f"✅ Updated failed items saved to {self.failed_items_file}")
        except Exception as e:
            print(f"❌ Error saving failed items: {e}")
    
    def log_retry_session(self, total_failed, successful_count, failed_count):
        """Log the retry session details."""
        try:
            with open(self.retry_log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n=== Retry Session: {timestamp} ===\n")
                f.write(f"Total failed items attempted: {total_failed}\n")
                f.write(f"Successfully retried: {successful_count}\n")
                f.write(f"Still failed: {failed_count}\n")
                f.write(f"Success rate: {successful_count/total_failed*100:.1f}%\n")
                f.write("=" * 50 + "\n")
        except Exception as e:
            print(f"Warning: Could not write to retry log: {e}")
    
    def run_retry(self):
        """Main method to run the retry process."""
        print("🔄 Starting failed items retry process...")
        
        # Load failed items and main data
        failed_items = self.load_failed_items()
        if not failed_items:
            print("No failed items to retry")
            return
        
        main_data = self.load_main_data()
        
        # Retry each failed item
        successful_retries = []
        still_failed = []
        
        for i, failed_item in enumerate(failed_items):
            print(f"\n[{i+1}/{len(failed_items)}] Processing failed item...")
            
            property_data, success = self.retry_failed_item(failed_item)
            
            if success and property_data:
                successful_retries.append(property_data)
            else:
                # Update failure count and timestamp
                failed_item['retry_attempts'] = failed_item.get('retry_attempts', 0) + 1
                failed_item['last_retry'] = time.strftime("%Y-%m-%d %H:%M:%S")
                still_failed.append(failed_item)
            
            # Small delay between retries to be respectful
            time.sleep(1)
        
        # Update main data with successful retries
        if successful_retries:
            main_data = self.update_main_data_with_retry(main_data, successful_retries)
            successful_project_ids = {item['property_id'] for item in successful_retries}
        else:
            successful_project_ids = set()
        
        # Save updated data
        self.save_data(main_data, still_failed)
        
        # Log the session
        self.log_retry_session(len(failed_items), len(successful_retries), len(still_failed))
        
        # Print summary
        print(f"\n🎉 Retry process completed!")
        print(f"📊 Results:")
        print(f"   Total failed items processed: {len(failed_items)}")
        print(f"   ✅ Successfully retried: {len(successful_retries)}")
        print(f"   ❌ Still failed: {len(still_failed)}")
        print(f"   📈 Success rate: {len(successful_retries)/len(failed_items)*100:.1f}%")
        
        if still_failed:
            print(f"\n⚠️  {len(still_failed)} items still failed and can be retried again")
        else:
            print(f"\n🎉 All failed items have been successfully retried!")


def main():
    """Main function to run the retry process."""
    retry_manager = FailedItemsRetry()
    retry_manager.run_retry()


if __name__ == "__main__":
    main()
