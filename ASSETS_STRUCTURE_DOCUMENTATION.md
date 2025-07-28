# Assets Structure and Data Optimization Documentation

## Overview

This document describes the optimized folder structure and JSON data format used in the Web Data Scraping project for Gurgaon properties. The system has been designed to minimize data duplication while maintaining efficient access to all assets and information.
```
**Only 2 property has been shown in the example. All will be in same format once confimed.**
```
## Assets Folder Structure

The assets are organized in a hierarchical structure under the `output/assets/` directory:

```
output/assets/
├── builders/
│   ├── {Builder_Name}_{ID}/
│   │   ├── logo/
│   │   │   └── {builder_logo_files}
│   │   └── team/
│   │       └── {team_member_photos}
├── locations/
│   ├── {Location_Name}_location_{ID}/
│   │   ├── location_image/
│   │   │   └── {location_photos}
│   │   └── neighbourhood/
│   │       └── {neighbourhood_icons}
└── projects/
    ├── common/
    │   └── amenities/
    │       ├── Sports/
    │       ├── Convenience/
    │       ├── Safety/
    │       ├── Leisure/
    │       └── Environment/
    └── {Project_Name}_{Property_ID}/
        ├── builder_info/
        │   └── logo/
        │       └── {builder_logo_for_this_project}
        ├── location_insights/
        │   └── icons/
        │       └── {location_insight_icons}
        ├── thumbnail/
        │   └── {project_thumbnail}
        ├── floor_plan_image/
        │   ├── 3_bhk/
        │   └── 4_bhk/
        ├── images/
        │   ├── Cover_Image/
        │   ├── Apartment_Interiors/
        │   ├── Amenities_Features/
        │   ├── Entrance_View/
        │   ├── Floor_Plans/
        │   ├── Master_Plan_Image/
        │   ├── 3_BHK/
        │   └── 4_BHK/
        └── videos/
            └── {project_videos}
```

## Key Optimization Features

### 1. **Project-Centric Organization**
- **Builder Info Assets**: Instead of maintaining separate global builder folders, each project contains its own `builder_info/logo/` folder
- **Location Insights Assets**: Each project has its own `location_insights/icons/` folder for location-specific icons
- **Benefit**: Easier project-specific deployments and maintenance

### 2. **Common Amenities Sharing**
- **Structure**: `assets/projects/common/amenities/`
- **Categories**: Sports, Convenience, Safety, Leisure, Environment etc....
- **Benefit**: Eliminates duplication of amenity icons across projects since most projects share similar amenities

### 3. **ID-Based Referencing System**
Instead of duplicating entire builder and location objects, the system uses unique IDs:

```json
{
  "projects": [
    {
      "property_id": "338549",
      "builder_info": {
        "builder_id": "494",
        "name": "Shapoorji Pallonji",
        "image": "assets/projects/Shapoorji_Pallonji_The_Dualis_338549/builder_info/logo/shapoorji_pallonji_494.jpg"
      },
      "location_insights": {
        "location_id": "location_1",
        "insights": [
          {
            "icon": "assets/projects/Shapoorji_Pallonji_The_Dualis_338549/location_insights/icons/key_insights_average_asking_price_icon.svg"
          }
        ]
      }
    }
  ],
  "builders": [
    {
      "id": "494",
      "name": "Shapoorji Pallonji",
      "logo": "assets/builders/Shapoorji_Pallonji_494/logo/shapoorji_pallonji_494.jpg"
    }
  ],
  "locations": [
    {
      "id": "location_1",
      "name": "Sector 46, Gurgaon",
      "image": "assets/locations/Sector_46__Gurgaon_location_1/location_image/sector_46_gurgaon.png"
    }
  ]
}
```

## JSON Structure Documentation

### Core Collections

#### 1. Projects Collection
```json
{
  "projects": [
    {
      "property_id": "string",
      "name": "string",
      "location": "string",
      "thumbnail_image": "local_asset_path",
      "price": "string",
      "price_insights": { /* pricing data */ },
      "status": "string",
      "information": { /* basic project info */ },
      "floor_plans": { /* floor plan images and details */ },
      "amenities": { /* amenity categories with icons */ },
      "specifications": [ /* project specifications */ ],
      "about": "html_content",
      "nearby_landmarks": { /* categorized nearby places */ },
      "location_insights": {
        "location_id": "reference_to_locations_collection",
        "description": "html_content",
        "insights": [
          {
            "icon": "project_specific_local_path",
            "text": "string"
          }
        ]
      },
      "builder_info": {
        "builder_id": "reference_to_builders_collection",
        "name": "string",
        "image": "project_specific_local_path",
        "total_projects": "string",
        "description": "string"
      },
      "all_media": {
        "images": { /* categorized project images */ },
        "videos": [ /* project videos */ ]
      }
    }
  ]
}
```

#### 2. Builders Collection
```json
{
  "builders": [
    {
      "id": "unique_builder_id",
      "name": "string",
      "logo": "assets/builders/{name}_{id}/logo/{filename}",
      "total_projects": "string",
      "experience": "string",
      "description": "string",
      "team": [
        {
          "name": "string",
          "designation": "string",
          "photo": "assets/builders/{name}_{id}/team/{filename}"
        }
      ]
    }
  ]
}
```

#### 3. Locations Collection
```json
{
  "locations": [
    {
      "id": "unique_location_id",
      "name": "string",
      "city": "string",
      "state": "string",
      "image": "assets/locations/{name}_location_{id}/location_image/{filename}",
      "neighbourhood_icons": [
        {
          "type": "string",
          "icon": "assets/locations/{name}_location_{id}/neighbourhood/{filename}"
        }
      ]
    }
  ]
}
```

## Asset Path Conventions

### 1. **Local Asset Paths**
All URLs are converted to local paths following these patterns:
- **Projects**: `assets/projects/{Project_Name}_{Property_ID}/{category}/{subcategory}/{filename}`
- **Builders**: `assets/builders/{Builder_Name}_{ID}/{category}/{filename}`
- **Locations**: `assets/locations/{Location_Name}_location_{ID}/{category}/{filename}`

### 2. **Common Assets**
- **Amenities**: `assets/projects/common/amenities/{category}/{filename}`
- Shared across all projects to avoid duplication

### 3. **Project-Specific Assets**
- **Builder Info**: `assets/projects/{Project_Name}_{Property_ID}/builder_info/logo/{filename}`
- **Location Insights**: `assets/projects/{Project_Name}_{Property_ID}/location_insights/icons/{filename}`

## Data Optimization Benefits

### 1. **Reduced Redundancy**
- **Builder Information**: Each unique builder is stored once in the `builders` collection
- **Location Data**: Each unique location is stored once in the `locations` collection
- **Amenity Icons**: Common amenity icons are shared across all projects

### 2. **Efficient Storage**
- **Before**: ~40MB+ with full duplication
- **After**: Estimated 60-70% size reduction through ID referencing and asset consolidation

### 3. **Maintainability**
- **Single Source of Truth**: Update builder/location info in one place
- **Consistent Asset Paths**: Standardized naming and folder structure
- **Easy Deployment**: Project-specific folders make selective deployment simple

### 4. **Scalability**
- **New Projects**: Simply reference existing builder/location IDs
- **New Builders/Locations**: Add once to respective collections
- **Asset Management**: Clear separation between global and project-specific assets

## Implementation Details

### Asset Download Process
1. **Project Assets**: Downloaded to project-specific folders
2. **Builder Assets**: Downloaded to both global builder folder and project-specific folder
3. **Location Assets**: Downloaded to both global location folder and project-specific folder
4. **Common Assets**: Downloaded once to common folder and referenced by all projects

### URL to Local Path Conversion
- All HTTP URLs are converted to local asset paths
- File extensions are preserved and standardized
- Folder names are sanitized to avoid filesystem issues
- Duplicate files are detected and skipped during download

## Usage Examples

### Accessing Builder Information
```javascript
// Find project
const project = data.projects.find(p => p.property_id === "338549");
const builderId = project.builder_info.builder_id;

// Get complete builder details
const builder = data.builders.find(b => b.id === builderId);

// Access builder logo from project-specific path
const projectBuilderLogo = project.builder_info.image;

// Access builder logo from global builder collection
const globalBuilderLogo = builder.logo;
```

### Accessing Location Information
```javascript
// Find project
const project = data.projects.find(p => p.property_id === "338549");
const locationId = project.location_insights.location_id;

// Get complete location details
const location = data.locations.find(l => l.id === locationId);

// Access location-specific assets
const locationImage = location.image;
const insightIcons = project.location_insights.insights.map(i => i.icon);
```

This optimized structure provides a clean, maintainable, and efficient way to manage real estate project data while minimizing storage requirements and maximizing data consistency.
