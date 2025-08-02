# Web Data Scraping - Project Structure

A well-organized real estate data scraping project with MongoDB integration.

## 📁 Project Structure

```
Web-Data-Scraping/
├── 📁 src/                          # Source code
│   ├── 📁 core/                     # Core application modules
│   │   ├── main.py                  # Main application entry point
│   │   ├── run.py                   # Application runner
│   │   └── config.py                # Configuration settings
│   ├── 📁 scrapers/                 # Web scraping modules
│   │   ├── scraper.py               # Main property scraper
│   │   ├── scraper_v1.py            # Version 1 scraper
│   │   ├── builder_information.py   # Builder data scraper
│   │   └── location_insights_scraper.py # Location data scraper
│   ├── 📁 utils/                    # Utility functions
│   │   └── utils.py                 # Common utility functions
│   └── 📁 media/                    # Media processing
│       ├── image_download.py        # Image downloader
│       ├── media_extractor.py       # Media extraction
│       └── media_extractor_selenium.py # Selenium-based extraction
│
├── 📁 mongodb/                      # MongoDB integration
│   ├── 📁 config/                   # MongoDB configuration
│   │   └── mongo_config.py          # MongoDB settings
│   └── 📁 importers/                # Data importers
│       ├── mongo_data_importer.py   # Main MongoDB importer
│       └── schema_mapping_report.py # Schema mapping analysis
│
├── 📁 tools/                        # Development tools
│   ├── 📁 error_tracking/           # Error tracking tools
│   │   ├── manual_404_tracker.py    # Manual 404 error tracker
│   │   ├── scan_404_errors.py       # Automated 404 scanner
│   │   ├── add_404_errors.py        # Add 404 errors to retry list
│   │   ├── check_failed_items.py    # Check failed items status
│   │   └── comprehensive_scan.py    # Comprehensive error scan
│   └── 📁 retry_system/             # Retry mechanisms
│       └── retry_failed_items.py    # Retry failed scraping items
│
├── 📁 scripts/                      # Utility scripts
│   └── 📁 utility/                  # General utility scripts
│       └── Data-Sample.json         # Sample data file
│
├── 📁 requirements/                 # Dependencies
│   ├── requirements.txt             # Main dependencies
│   ├── requirements_mongo.txt       # MongoDB dependencies
│   └── requirements_RH.txt          # Red Hat specific dependencies
│
├── 📁 docs/                         # Documentation
│   ├── README.md                    # Main project documentation
│   ├── MONGODB_IMPORT_GUIDE.md      # MongoDB import guide
│   ├── SCHEMA_MAPPING_SUMMARY.md    # Schema mapping documentation
│   └── ASSETS_STRUCTURE_DOCUMENTATION.md # Assets structure guide
│
├── 📁 output/                       # Generated output files
│   ├── gurgaon_properties_with_local_assets.json
│   ├── download_log.txt
│   └── 📁 assets/                   # Downloaded assets
│       ├── 📁 builders/             # Builder images and assets
│       ├── 📁 locations/            # Location images
│       └── 📁 projects/             # Project images and floor plans
│
├── 📁 tests/                        # Test files (future)
├── run_scraper.py                   # Main entry point
└── .gitignore                       # Git ignore file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements/requirements.txt
```

### 2. Run the Scraper
```bash
python run_scraper.py
```

### 3. Download Images (Optional)
```bash
python run_image_download.py
# OR alternatively:
python src/media/image_download.py
```

### 4. MongoDB Import (Optional)
```bash
# First install MongoDB dependencies
pip install -r requirements/requirements_mongo.txt

# Then run the import
python mongodb/run_mongo_import.py
```

## 📖 Module Descriptions

### Core Modules (`src/core/`)
- **main.py**: Main application logic
- **run.py**: Application runner with configuration
- **config.py**: Global configuration settings

### Scrapers (`src/scrapers/`)
- **scraper.py**: Enhanced property scraper with error handling
- **builder_information.py**: Extracts builder/developer information
- **location_insights_scraper.py**: Scrapes location-based insights

### Media Processing (`src/media/`)
- **image_download.py**: Multi-threaded image downloader
- **media_extractor.py**: Media extraction utilities
- **media_extractor_selenium.py**: Selenium-based media extraction

### MongoDB Integration (`mongodb/`)
- **importers/mongo_data_importer.py**: Complete MongoDB data importer
- **importers/schema_mapping_report.py**: Schema mapping analysis
- **config/mongo_config.py**: MongoDB configuration

### Development Tools (`tools/`)
- **error_tracking/**: Tools for tracking and managing scraping errors
- **retry_system/**: System for retrying failed scraping operations

## 🔧 Configuration

Configuration files are located in `src/core/config.py`. Key settings:
- `MAX_WORKERS`: Number of concurrent threads
- `MAX_RETRIES`: Maximum retry attempts
- `RETRY_DELAY`: Delay between retry attempts

## 📊 Data Flow

1. **Scraping**: `src/scrapers/scraper.py` → Raw data
2. **Media Download**: `src/media/image_download.py` → Asset files
3. **Error Tracking**: `tools/error_tracking/` → Failed items tracking
4. **Retry System**: `tools/retry_system/` → Retry failed operations
5. **MongoDB Import**: `mongodb/importers/` → Database storage

## 🛠️ Development

### Adding New Scrapers
1. Create new file in `src/scrapers/`
2. Follow existing patterns from `scraper.py`
3. Update imports in main application

### Adding New Tools
1. Create appropriate subdirectory in `tools/`
2. Follow existing tool patterns
3. Document usage in this README

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:
- MongoDB integration guide
- Schema mapping documentation
- Assets structure documentation

## 🔍 Troubleshooting

1. **Import Errors**: Ensure Python path includes `src/` directory
2. **Missing Dependencies**: Install from appropriate requirements file
3. **MongoDB Issues**: Check `mongodb/config/mongo_config.py` settings
4. **Failed Scraping**: Use tools in `tools/error_tracking/` to diagnose

## 🚀 Future Enhancements

- [ ] Add test suite in `tests/` directory
- [ ] Implement logging configuration
- [ ] Add CI/CD pipeline
- [ ] Create Docker containerization
- [ ] Add performance monitoring

---

**Note**: This organized structure makes the project more maintainable, scalable, and easier to understand for new developers.
