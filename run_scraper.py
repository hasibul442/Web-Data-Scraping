#!/usr/bin/env python3
"""
Web Data Scraping - Main Entry Point
Organized project structure for real estate data scraping.
"""

import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main application entry point with error handling."""
    print("=" * 50)
    print("🏠 Real Estate Data Scraper")
    print("=" * 50)
    
    try:
        # Try to import and run the main scraper
        from core.main import main as run_main
        run_main()
        
    except ImportError as e:
        print(f"⚠️  Could not import core.main: {e}")
        print("Trying alternative entry points...")
        
        try:
            # Try run.py as alternative
            from core.run import main as run_alternative
            run_alternative()
        except ImportError:
            try:
                # Try direct scraper import
                from scrapers.scraper import main as scraper_main
                scraper_main()
            except ImportError:
                print("❌ Could not find any valid entry point.")
                print("Please check that the following files exist:")
                print("  - src/core/main.py")
                print("  - src/core/run.py")
                print("  - src/scrapers/scraper.py")
                return False
                
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return False
    
    print("\n✅ Scraping completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
