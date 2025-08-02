#!/usr/bin/env python3
"""
MongoDB Import - Entry Point
Run this script to import scraped JSON data into MongoDB.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def main():
    """Main MongoDB import entry point."""
    print("=" * 50)
    print("🗄️  MongoDB Data Importer")
    print("=" * 50)
    
    try:
        # Import the MongoDB importer
        from mongodb.importers.mongo_data_importer import MongoDataImporter
        
        # Default input file (can be customized)
        input_file = os.path.join(project_root, 'output', 'gurgaon_properties_with_local_assets.json')
        
        if not os.path.exists(input_file):
            print(f"❌ Input file not found: {input_file}")
            print("Please ensure you have scraped data first by running:")
            print("python run_scraper.py")
            return False
        
        # Create importer and run
        importer = MongoDataImporter()
        results = importer.import_data(input_file)
        
        if results:
            print("✅ MongoDB import completed successfully!")
            print(f"📊 Import Summary:")
            total_imported = 0
            for collection, count in results.items():
                if collection != 'errors':
                    print(f"   - {collection}: {count} documents")
                    total_imported += count
                elif collection == 'errors' and count > 0:
                    print(f"   - ⚠️  errors: {count}")
            
            if results.get('errors', 0) == 0:
                print("🎉 All data imported without errors!")
            else:
                print(f"⚠️  Import completed with {results['errors']} errors")
            
            return True
        else:
            print("❌ MongoDB import failed!")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure MongoDB dependencies are installed:")
        print("pip install -r requirements/requirements_mongo.txt")
        return False
    except Exception as e:
        print(f"❌ Error during import: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
