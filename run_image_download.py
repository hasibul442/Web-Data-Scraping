#!/usr/bin/env python3
"""
Image Download - Entry Point
Run this script to download all images from scraped property data.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    """Main image download entry point."""
    print("=" * 50)
    print("📸 Real Estate Image Downloader")
    print("=" * 50)
    
    try:
        # Import the image downloader
        from media.image_download import main as image_download_main
        
        # Check if input file exists
        input_file = os.path.join(project_root, 'output', 'gurgaon_properties.json')
        
        if not os.path.exists(input_file):
            print(f"❌ Input file not found: {input_file}")
            print("Please ensure you have scraped data first by running:")
            print("python run_scraper.py")
            return False
        
        # Run the image downloader
        success = image_download_main()
        
        if success:
            print("✅ Image download completed successfully!")
            return True
        else:
            print("⚠️  Image download completed with some issues")
            return True  # Still consider success as some downloads might have failed
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements/requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error during image download: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
