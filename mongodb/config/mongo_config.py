#!/usr/bin/env python3
"""
MongoDB Configuration
"""

import os
from typing import Dict, Any

# MongoDB Configuration
MONGODB_CONFIG = {
    "uri": os.getenv("MONGODB_URI", "mongodb+srv://starjahidbd_db_user:RUTGjci34AmU5DlP@cluster0.b7lygfq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"),
    "database": os.getenv("MONGODB_DATABASE", "gurgaon_commercial"),
    "collections": {
        "projects": "projects",
        "developers": "developers", 
        "locations": "locations",
        "project_meta": "project_meta"
    }
}

# Schema Mapping Configuration
SCHEMA_MAPPINGS = {
    "project": {
        # Direct mappings
        "property_id": "projectId",
        "location": "location",
        "about": "description",
        "status": "propertyStatus",
        
        # Nested mappings
        "builder_info.builder_id": "developerId",
        "location_insights.location_id": "projectLocationId",
        
        # Complex mappings (handled in code)
        "information": "highlights",
        "amenities": "amenities",
        "price_list": "priceList",
        "thumbnail_image": "projectImages.coverImage"
    },
    
    "developer": {
        "id": "developerId",
        "name": "name",
        "overview": "description",
        "customer_care_number": "customer_care_number",
        "image.src": "image",
        "projects": "projects",
        "faq": "faq"
    },
    
    "location": {
        "id": "projectLocationId", 
        "location_name": "location_name",
        "about_sector.overview": "description",
        "indices": "indices",
        "demand_supply": "demand",
        "price_insights": "price_insights"
    }
}

# Default values for missing fields
DEFAULT_VALUES = {
    "project": {
        "countryId": "IN",
        "stateId": "HR", 
        "city": "Gurgaon",
        "status": 1,
        "propertyPurpose": "Residential",
        "buildingType": "Apartment",
        "propertyType": "Project",
        "propertySaleType": "New",
        "category": "Residential"
    },
    
    "developer": {
        "projects": {
            "on_going": "0",
            "past": "0", 
            "total": "0"
        }
    },
    
    "location": {
        "indices": {
            "heading": "",
            "content": "",
            "rating": ""
        }
    }
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration."""
    return {
        "mongodb": MONGODB_CONFIG,
        "mappings": SCHEMA_MAPPINGS,
        "defaults": DEFAULT_VALUES
    }
