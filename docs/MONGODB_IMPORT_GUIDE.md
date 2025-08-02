# MongoDB Data Importer

This script converts the scraped real estate JSON data to MongoDB collections following the provided schemas.

## Prerequisites

1. **Install MongoDB** (if not already installed)
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements_mongo.txt
   ```

## Usage

### Quick Start
```bash
python mongo_data_importer.py
```

### Configuration

The script uses these default settings:
- **MongoDB URI**: `mongodb://localhost:27017`
- **Database**: `gurgaon_real_estate`
- **Collections**: `projects`, `developers`, `locations`, `project_meta`

To customize, set environment variables:
```bash
export MONGODB_URI="mongodb://your-host:27017"
export MONGODB_DATABASE="your_database"
```

## Schema Mapping

### ✅ Successfully Mapped Fields

#### Projects (ProjectDetailSchema)
- `property_id` → `projectId`
- `builder_info.builder_id` → `developerId`
- `location` → `location/fullAddress`
- `about` → `description`
- `status` → `propertyStatus`
- `information` → `highlights` (converted to key-value pairs)
- `amenities` → `amenities` (flattened array)
- `price_list` → `priceList` (with floor plans)
- `thumbnail_image` → `projectImages.coverImage`

#### Developers (BuilderSchema)
- `id` → `developerId`
- `name` → `name`
- `image.src` → `image`
- `projects` → `projects`
- `overview` → `description`
- `customer_care_number` → `customer_care_number`
- `faq` → `faq`

#### Locations (LocationSchema)
- `id` → `projectLocationId`
- `location_name` → `location_name`
- `about_sector.overview` → `description`
- `indices` → `indices`
- `demand_supply` → `demand`
- `price_insights` → `price_insights`

### ⚠️ Missing in Source Data

#### Projects
- `lat/lng` (coordinates)
- `zipcode`
- `propertyAge`
- `unitNo`
- `expectedPossession`
- `bathroom/balcony/parking` (at project level)

#### Developers
- Most fields are available or can be extracted

#### Locations
- Most fields are available

### 🆕 Additional Fields Available (Not in Schema)

#### Projects
- `price_insights` (rental supply, comparable projects)
- `specifications` (detailed building specs)
- `nearby_landmarks` (schools, hospitals, etc.)
- `location_insights`
- `rera` (registration details)
- `all_media` (images, videos)

#### Developers
- `experience`
- `head_office_address`
- `branch_office_address`
- `company_size`
- `management_team`
- `key_service_and_specialities`
- `awards_and_recognition`
- `projects_in_top_cities`

#### Locations
- `rank` (locality ranking)
- `average_sale_price`
- `average_rental`
- `new_project_count`
- `properties_for_sale_count`
- `properties_for_rent_count`
- `neighbourhood` (nearby amenities)

## Output

The script will:
1. Connect to MongoDB
2. Create/update collections
3. Import all data with proper schema mapping
4. Generate a detailed mapping report
5. Provide import statistics

## Collections Created

1. **projects** - Main project/property data
2. **developers** - Builder/developer information  
3. **locations** - Location insights and data
4. **project_meta** - Meta information (amenities, categories, etc.)

## Notes

- The script uses `upsert` operations to avoid duplicates
- Data types are preserved (arrays, objects remain as-is)
- HTML content is converted to plain text where appropriate
- Missing schema fields are handled gracefully
- Additional source fields are noted but not lost
