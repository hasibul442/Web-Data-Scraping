"""
Alternative main runner for the property scraper.
Runs the main scraper and then the image downloader.
"""

import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def main():
    """Run the complete scraping and image download process."""
    print("🚀 Running complete scraping process...")
    
    try:
        # Import and run main scraper
        from core.main import main as run_main_scraper
        print("📊 Step 1: Running main scraper...")
        run_main_scraper()
        
        # Import and run image downloader
        from media.image_download import main as run_image_download
        print("\n📸 Step 2: Running image downloader...")
        run_image_download()
        
        print("\n✅ Complete scraping process finished successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
        return False
    except Exception as e:
        print(f"❌ Error during scraping process: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)