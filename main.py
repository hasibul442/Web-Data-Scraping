# Main script to run the property scraper

from scraper import PropertyScraper
from utils import save_to_json, flatten_list_of_lists
from config import MAX_WORKERS, OUTPUT_FILE, START_PAGE, END_PAGE, ENCODING

def main():
    """Main function to run the property scraper."""
    print("Starting Gurgaon Properties Scraper")
    print("=" * 40)
    
    # Initialize the scraper
    scraper = PropertyScraper()
    
    # Define pages to scrape
    pages = list(range(START_PAGE, END_PAGE + 1))
    print(f"Scraping pages {START_PAGE} to {END_PAGE}")
    
    # Scrape the pages
    try:
        results = scraper.scrape_multiple_pages(pages, max_workers=MAX_WORKERS)
        
        if results:
            # Save results to JSON
            success = save_to_json(results, OUTPUT_FILE, ENCODING)
            
            if success:
                print(f"\nScraping completed successfully!")
                print(f"Total properties scraped: {len(results)}")
                print(f"Results saved to: {OUTPUT_FILE}")
            else:
                print(f"\nScraping completed but failed to save results to {OUTPUT_FILE}")
        else:
            print("\nNo data was scraped. Please check the website or your configuration.")
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred during scraping: {e}")

if __name__ == "__main__":
    main()
