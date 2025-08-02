#!/usr/bin/env python3
"""
MongoDB Data Importer
Converts scraped JSON data to MongoDB collections following the provided schemas.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class MongoDataImporter:
    """
    Handles conversion and insertion of scraped real estate data into MongoDB collections.
    Maps JSON structure to provided MongoDB schemas for projects, developers, and locations.
    """
    
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017", database_name: str = "gurgaon_real_estate"):
        """Initialize MongoDB connection and collections."""
        try:
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[database_name]
            
            # Collections
            self.projects_collection = self.db.projects
            self.developers_collection = self.db.developers  # builders
            self.locations_collection = self.db.locations
            self.project_meta_collection = self.db.project_meta
            
            print(f"✅ Connected to MongoDB: {database_name}")
        except PyMongoError as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
    
    def load_json_data(self, file_path: str) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"❌ Failed to load JSON file: {e}")
            raise
    
    def extract_price_amount(self, price_str: str) -> Optional[str]:
        """Extract price amount from string like '₹ 4.83 Cr'."""
        if not price_str:
            return None
        # Remove currency symbols and extract numeric part
        cleaned = re.sub(r'[₹,\s]', '', price_str)
        return cleaned if cleaned else None
    
    def extract_area_sqft(self, area_str: str) -> Optional[float]:
        """Extract square feet from area string."""
        if not area_str:
            return None
        match = re.search(r'(\d+(?:\.\d+)?)', area_str.replace(',', ''))
        return float(match.group(1)) if match else None
    
    def extract_bedroom_count(self, unit_type: str) -> Optional[str]:
        """Extract bedroom count from unit type."""
        if not unit_type:
            return None
        match = re.search(r'(\d+)\s*BHK', unit_type, re.IGNORECASE)
        return match.group(1) if match else None
    
    def map_project_to_schema(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Map scraped project data to ProjectDetailSchema."""
        
        # Map basic fields
        mapped_project = {
            "projectId": project.get("property_id"),
            "developerId": project.get("builder_info", {}).get("builder_id"),
            "countryId": "IN",  # Assuming India
            "stateId": "HR",    # Haryana for Gurgaon
            "city": "Gurgaon",
            "description": project.get("about", ""),
            "location": project.get("location", ""),
            "fullAddress": project.get("location", ""),
            "lat": None,  # Not available in current data
            "lng": None,  # Not available in current data
            "projectLocationId": project.get("location_insights", {}).get("location_id"),
            "zipcode": None,  # Not available
            "propertyAge": None,  # Not available
            "unitNo": None,  # Not available
            "status": 1,  # Active
            "propertyPurpose": "Residential",  # Inferred
            "buildingType": "Apartment",  # Inferred from data
            "propertyType": "Project",  # Inferred
            "propertyStatus": project.get("status", ""),
            "expectedPossession": None,  # Not directly available
            "propertySaleType": "New",  # Inferred
            "category": "Residential",  # Inferred
            "highlights": self._map_highlights(project),
            "furnishingType": None,  # Not available
            "amenities": self._map_amenities(project.get("amenities", {})),
            "bathroom": None,  # Not available at project level
            "balcony": None,   # Not available at project level
            "parking": None,   # Not available at project level
            "buildupArea": self._extract_total_area(project.get("information", {})),
            "AssignTo": None,
            "AssignToUser": None,
            "priceList": self._map_price_list(project),
            "projectImages": self._map_project_images(project)
        }
        
        return {k: v for k, v in mapped_project.items() if v is not None}
    
    def _map_highlights(self, project: Dict[str, Any]) -> List[Dict[str, str]]:
        """Map project information to highlights."""
        highlights = []
        info = project.get("information", {})
        
        if info.get("unit_config"):
            highlights.append({
                "key": "Unit Configuration",
                "value": info["unit_config"]
            })
        
        if info.get("size"):
            highlights.append({
                "key": "Size Range",
                "value": info["size"]
            })
        
        if info.get("units"):
            highlights.append({
                "key": "Total Units",
                "value": str(info["units"])
            })
        
        if info.get("total_area"):
            highlights.append({
                "key": "Total Area",
                "value": info["total_area"]
            })
        
        return highlights
    
    def _map_amenities(self, amenities: Dict[str, List]) -> List[Dict[str, Any]]:
        """Map amenities structure to AmenityCategorySchema format."""
        amenity_list = []
        for category, items in amenities.items():
            for item in items:
                if isinstance(item, dict) and item.get("name"):
                    amenity_list.append({
                        "categoryName": category,
                        "name": item["name"],
                        "icon": item.get("icon", ""),
                        "status": True
                    })
        return amenity_list
    
    def _extract_total_area(self, info: Dict[str, Any]) -> Optional[float]:
        """Extract total area from information."""
        total_area = info.get("total_area", "")
        if total_area:
            match = re.search(r'(\d+(?:\.\d+)?)', str(total_area))
            return float(match.group(1)) if match else None
        return None
    
    def _map_price_list(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map price list with floor plans."""
        price_list = []
        
        # Get price list from project
        project_prices = project.get("price_list", [])
        floor_plans = project.get("floor_plans", {})
        
        for price_item in project_prices:
            unit_type = price_item.get("unit_type", "")
            bedroom = self.extract_bedroom_count(unit_type)
            
            # Find corresponding floor plan
            floor_plan_images = self._find_floor_plan_images(bedroom, floor_plans)
            
            price_entry = {
                "propertyType": "Apartment",
                "bedroom": bedroom,
                "carpetArea": self.extract_area_sqft(unit_type),
                "price": price_item.get("price"),
                "floorPlan": floor_plan_images
            }
            
            price_list.append({k: v for k, v in price_entry.items() if v is not None})
        
        return price_list
    
    def _find_floor_plan_images(self, bedroom: str, floor_plans: Dict) -> List[Dict]:
        """Find floor plan images for specific bedroom configuration."""
        if not bedroom:
            return []
        
        bhk_key = f"{bedroom}_bhk"
        plans = floor_plans.get(bhk_key, [])
        
        floor_plan_data = []
        for plan in plans:
            if plan.get("2d_src"):
                floor_plan_data.append({
                    "type": "2D",
                    "images": [plan["2d_src"]]
                })
            if plan.get("3d_src"):
                floor_plan_data.append({
                    "type": "3D",
                    "images": [plan["3d_src"]]
                })
        
        return floor_plan_data
    
    def _map_project_images(self, project: Dict[str, Any]) -> Dict[str, List[str]]:
        """Map project images."""
        images = {
            "coverImage": [],
            "masterPlan": [],
            "locationImage": [],
            "amenitiesImage": [],
            "pushCreative": [],
            "brochure": [],
            "videos": []
        }
        
        # Add thumbnail as cover image
        if project.get("thumbnail_image"):
            images["coverImage"].append(project["thumbnail_image"])
        
        # Add videos from all_media
        all_media = project.get("all_media", {})
        if all_media.get("videos"):
            images["videos"] = all_media["videos"]
        
        return images
    
    def map_developer_to_schema(self, builder: Dict[str, Any]) -> Dict[str, Any]:
        """Map scraped builder data to developer schema."""
        
        mapped_developer = {
            "developerId": builder.get("id"),
            "name": builder.get("name"),
            "image": self._extract_image_src(builder.get("image", {})),
            "projects": self._map_developer_projects(builder.get("projects", {})),
            "head_office_address": builder.get("head_office_address", {}),
            "branch_office_address": builder.get("branch_office_address", []),
            "description": builder.get("overview", ""),
            # "specialities": self._extract_text_from_html(builder.get("key_service_and_specialities")),
            "specialities": builder.get("key_service_and_specialities"),
            # "awards": self._extract_text_from_html(builder.get("awards_and_recognition")),
            "awards": builder.get("awards_and_recognition"),
            "customer_care_number": builder.get("customer_care_number"),
            "company_size": self._extract_company_size(builder.get("company_size")),
            "experience": builder.get("experience"),
            "management_team": builder.get("management_team"),
            "faq": self._map_faq_array(builder.get("faq", []))
        }
        
        return {k: v for k, v in mapped_developer.items() if v is not None}
    
    def _extract_image_src(self, image: Dict[str, Any]) -> Optional[str]:
        """Extract image source from image object."""
        if isinstance(image, dict):
            return image.get("src")
        return str(image) if image else None
    
    def _map_developer_projects(self, projects: Dict[str, Any]) -> Dict[str, str]:
        """Map developer projects data."""
        return {
            "on_going": str(projects.get("on_going", 0)),
            "past": str(projects.get("past", 0)),
            "total": str(projects.get("total", 0))
        }
    
    def _extract_text_from_html(self, html_content: Optional[str]) -> Optional[str]:
        """Extract plain text from HTML content."""
        if not html_content:
            return None
        # Simple HTML tag removal
        text = re.sub(r'<[^>]+>', '', str(html_content))
        return text.strip() if text.strip() else None
    
    def _extract_company_size(self, company_size: Any) -> Optional[int]:
        """Extract company size number."""
        if isinstance(company_size, dict):
            size_str = company_size.get("company_size", "")
            if size_str and size_str.isdigit():
                return int(size_str)
        elif isinstance(company_size, (int, str)) and str(company_size).isdigit():
            return int(company_size)
        return None
    
    def _map_faq_array(self, faq_data: List[Dict]) -> List[Dict[str, str]]:
        """Map FAQ data to array of objects with question and answer keys."""
        if not faq_data:
            return []
        
        faq_array = []
        for faq_item in faq_data:
            if isinstance(faq_item, dict):
                # Handle different possible FAQ structures
                if faq_item.get("question") and faq_item.get("answer"):
                    faq_array.append({
                        "question": str(faq_item["question"]),
                        "answer": str(faq_item["answer"])
                    })
                elif faq_item.get("q") and faq_item.get("a"):
                    faq_array.append({
                        "question": str(faq_item["q"]),
                        "answer": str(faq_item["a"])
                    })
                elif len(faq_item) >= 2:
                    # If it's a dict with unknown keys, take first two values
                    keys = list(faq_item.keys())
                    faq_array.append({
                        "question": str(faq_item[keys[0]]),
                        "answer": str(faq_item[keys[1]])
                    })
        
        return faq_array
    
    def map_location_to_schema(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Map scraped location data to location schema."""
        
        mapped_location = {
            "projectLocationId": location.get("id"),
            "location_name": location.get("location_name"),
            "description": self._extract_text_from_html(
                location.get("about_sector", {}).get("overview")
            ),
            "indices": self._map_location_indices(location.get("indices", [])),
            "demand": self._map_demand_supply(location.get("demand_supply", {})),
            "price_insights": location.get("price_insights", {})
        }
        
        return {k: v for k, v in mapped_location.items() if v is not None}
    
    def _map_location_indices(self, indices: List[Dict]) -> Dict[str, str]:
        """Map location indices to schema format."""
        if not indices:
            return {}
        
        # Take first index as primary or combine all
        primary_index = indices[0] if indices else {}
        return {
            "heading": primary_index.get("heading", ""),
            "content": "; ".join([idx.get("heading", "") for idx in indices]),
            "rating": primary_index.get("rating", "")
        }
    
    def _map_demand_supply(self, demand_supply: Dict) -> Dict[str, str]:
        """Map demand supply data."""
        sale_data = demand_supply.get("sale", {})
        
        return {
            "type": "Mixed",  # Default
            "by_property": json.dumps(sale_data.get("by_property_type", [])),
            "by_bhk": json.dumps(sale_data.get("by_bhk", [])),
            "by_budget": json.dumps(sale_data.get("by_budget", []))
        }
    
    def create_project_meta(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Create project meta data for a single project."""
        
        # Extract amenities with categories for this project
        amenities = []
        amenity_categories = set()
        
        project_amenities = project.get("amenities", {})
        for category, items in project_amenities.items():
            amenity_categories.add(category)
            for item in items:
                if isinstance(item, dict) and item.get("name"):
                    amenities.append({
                        "categoryName": category,
                        "name": item["name"],
                        "icon": item.get("icon", ""),
                        "status": True
                    })
        
        # Extract bedrooms from this project's price list
        bedrooms = set()
        property_statuses = set()
        
        # Extract bedrooms from price list
        for price_item in project.get("price_list", []):
            unit_type = price_item.get("unit_type", "")
            bedroom = self.extract_bedroom_count(unit_type)
            if bedroom:
                bedrooms.add(f"{bedroom} BHK")
        
        # Extract property status
        if project.get("status"):
            property_statuses.add(project["status"])
        
        meta_schema = {
            "projectId": project.get("property_id"),  # Link to specific project
            "propertyPurpose": [{"name": "Residential", "icon": "", "status": True}],
            "buildingType": [{"name": "Apartment", "icon": "", "status": True}],
            "propertyType": [{"name": "Project", "icon": "", "status": True}],
            "bedrooms": [{"name": br, "icon": "", "status": True} for br in sorted(bedrooms)],
            "propertyStatus": [{"name": status, "icon": "", "status": True} for status in property_statuses],
            "propertySaleType": [{"name": "New Launch", "icon": "", "status": True}],
            "expectedPossession": [{"name": "Under Construction", "icon": "", "status": True}],
            "furnishingType": [{"name": "Unfurnished", "icon": "", "status": True}],
            "highlights": [{"name": "Premium Location", "icon": "", "status": True}],
            "categories": [{"name": cat, "icon": "", "status": True} for cat in amenity_categories],
            "amenities": amenities
        }
        
        return meta_schema
    
    def import_data(self, json_file_path: str):
        """Main method to import all data to MongoDB."""
        print(f"🚀 Starting data import from {json_file_path}")
        
        # Load data
        data = self.load_json_data(json_file_path)
        
        results = {
            "projects": 0,
            "developers": 0,
            "locations": 0,
            "project_meta": 0,
            "errors": 0
        }
        
        # Create mapping dictionaries for foreign key relationships
        developer_id_mapping = {}  # original_id -> MongoDB _id
        location_id_mapping = {}   # original_id -> MongoDB _id
        
        # Import Developers (Builders) and build ID mapping
        print("\n📁 Importing Developers...")
        builders = data.get("builders", [])
        for builder in builders:
            try:
                mapped_developer = self.map_developer_to_schema(builder)
                if mapped_developer.get("developerId"):
                    # Use upsert to get the MongoDB document
                    result = self.developers_collection.update_one(
                        {"developerId": mapped_developer["developerId"]},
                        {"$set": mapped_developer},
                        upsert=True
                    )
                    
                    # Get the actual MongoDB _id
                    if result.upserted_id:
                        mongo_id = result.upserted_id
                    else:
                        # Document was updated, find it to get _id
                        doc = self.developers_collection.find_one({"developerId": mapped_developer["developerId"]})
                        mongo_id = doc["_id"]
                    
                    # Store mapping: original_id -> MongoDB _id
                    developer_id_mapping[mapped_developer["developerId"]] = mongo_id
                    
                    results["developers"] += 1
                    print(f"✅ Developer: {mapped_developer.get('name', 'Unknown')} (ID: {mongo_id})")
                else:
                    print(f"⚠️  Skipped developer without ID: {builder.get('name', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error importing developer {builder.get('name', 'Unknown')}: {e}")
                results["errors"] += 1
        
        # Import Locations and build ID mapping
        print("\n🗺️  Importing Locations...")
        locations = data.get("locations", [])
        for location in locations:
            try:
                mapped_location = self.map_location_to_schema(location)
                if mapped_location.get("projectLocationId"):
                    # Use upsert to get the MongoDB document
                    result = self.locations_collection.update_one(
                        {"projectLocationId": mapped_location["projectLocationId"]},
                        {"$set": mapped_location},
                        upsert=True
                    )
                    
                    # Get the actual MongoDB _id
                    if result.upserted_id:
                        mongo_id = result.upserted_id
                    else:
                        # Document was updated, find it to get _id
                        doc = self.locations_collection.find_one({"projectLocationId": mapped_location["projectLocationId"]})
                        mongo_id = doc["_id"]
                    
                    # Store mapping: original_id -> MongoDB _id
                    location_id_mapping[mapped_location["projectLocationId"]] = mongo_id
                    
                    results["locations"] += 1
                    print(f"✅ Location: {mapped_location.get('location_name', 'Unknown')} (ID: {mongo_id})")
                else:
                    print(f"⚠️  Skipped location without ID: {location.get('location_name', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error importing location {location.get('location_name', 'Unknown')}: {e}")
                results["errors"] += 1
        
        # Import Projects with proper foreign key references
        print("\n🏗️  Importing Projects...")
        projects = data.get("projects", [])
        for project in projects:
            try:
                mapped_project = self.map_project_to_schema(project)
                if mapped_project.get("projectId"):
                    
                    # Replace developerId with MongoDB _id reference
                    original_developer_id = mapped_project.get("developerId")
                    if original_developer_id and original_developer_id in developer_id_mapping:
                        mapped_project["developerId"] = developer_id_mapping[original_developer_id]
                        print(f"🔗 Linked project to developer ID: {developer_id_mapping[original_developer_id]}")
                    else:
                        print(f"⚠️  Developer reference not found for project: {project.get('name', 'Unknown')}")
                        mapped_project["developerId"] = None
                    
                    # Replace projectLocationId with MongoDB _id reference
                    original_location_id = mapped_project.get("projectLocationId")
                    if original_location_id and original_location_id in location_id_mapping:
                        mapped_project["projectLocationId"] = location_id_mapping[original_location_id]
                        print(f"🔗 Linked project to location ID: {location_id_mapping[original_location_id]}")
                    else:
                        print(f"⚠️  Location reference not found for project: {project.get('name', 'Unknown')}")
                        mapped_project["projectLocationId"] = None
                    
                    self.projects_collection.update_one(
                        {"projectId": mapped_project["projectId"]},
                        {"$set": mapped_project},
                        upsert=True
                    )
                    results["projects"] += 1
                    print(f"✅ Project: {project.get('name', 'Unknown')}")
                else:
                    print(f"⚠️  Skipped project without ID: {project.get('name', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error importing project {project.get('name', 'Unknown')}: {e}")
                results["errors"] += 1
        
        # Create and Import Project Meta (one per project)
        print("\n📊 Creating Project Meta for each project...")
        try:
            for project in projects:
                if project.get("property_id"):
                    meta_data = self.create_project_meta(project)
                    self.project_meta_collection.update_one(
                        {"projectId": meta_data["projectId"]},
                        {"$set": meta_data},
                        upsert=True
                    )
                    results["project_meta"] += 1
                    print(f"✅ Project Meta created for: {project.get('name', meta_data['projectId'])}")
            print(f"✅ Created {results['project_meta']} Project Meta documents")
        except Exception as e:
            print(f"❌ Error creating project meta: {e}")
            results["errors"] += 1
        
        return results, developer_id_mapping, location_id_mapping
    
    def print_foreign_key_summary(self, developer_mapping: Dict, location_mapping: Dict):
        """Print summary of foreign key relationships created."""
        print("\n" + "="*60)
        print("🔗 FOREIGN KEY RELATIONSHIPS")
        print("="*60)
        
        print(f"\n👥 Developer ID Mappings ({len(developer_mapping)} total):")
        for original_id, mongo_id in developer_mapping.items():
            print(f"  • {original_id} → {mongo_id}")
        
        print(f"\n🗺️  Location ID Mappings ({len(location_mapping)} total):")
        for original_id, mongo_id in location_mapping.items():
            print(f"  • {original_id} → {mongo_id}")
        
        print("\n📋 Collections Schema:")
        print("  • projects.developerId → developers._id")
        print("  • projects.projectLocationId → locations._id")
        print("="*60)
    
    def print_schema_mapping_report(self, json_file_path: str):
        """Print detailed report of schema mapping."""
        data = self.load_json_data(json_file_path)
        
        print("\n" + "="*80)
        print("📋 SCHEMA MAPPING REPORT")
        print("="*80)
        
        # Analyze projects
        if data.get("projects"):
            sample_project = data["projects"][0]
            print("\n🏗️  PROJECT SCHEMA MAPPING:")
            print("-" * 40)
            
            print("✅ MAPPED FIELDS:")
            mapped_fields = [
                "property_id → projectId",
                "builder_info.builder_id → developerId", 
                "location → location/fullAddress",
                "about → description",
                "status → propertyStatus",
                "information → highlights",
                "amenities → amenities (flattened)",
                "price_list → priceList",
                "thumbnail_image → projectImages.coverImage"
            ]
            for field in mapped_fields:
                print(f"  • {field}")
            
            print("\n⚠️  MISSING IN SOURCE DATA:")
            missing_fields = [
                "lat/lng (coordinates)",
                "zipcode",
                "propertyAge",
                "unitNo",
                "expectedPossession",
                "bathroom/balcony/parking (project level)",
                "buildupArea (need to parse from information)"
            ]
            for field in missing_fields:
                print(f"  • {field}")
            
            print("\n🆕 NEW FIELDS IN SOURCE:")
            new_fields = [
                "price_insights",
                "specifications", 
                "nearby_landmarks",
                "location_insights",
                "rera",
                "faq",
                "all_media"
            ]
            for field in new_fields:
                print(f"  • {field}")
        
        # Analyze developers/builders
        if data.get("builders"):
            print("\n👥 DEVELOPER SCHEMA MAPPING:")
            print("-" * 40)
            
            print("✅ MAPPED FIELDS:")
            mapped_dev_fields = [
                "id → developerId",
                "name → name",
                "image.src → image",
                "projects → projects",
                "overview → description",
                "customer_care_number → customer_care_number",
                "faq → faq"
            ]
            for field in mapped_dev_fields:
                print(f"  • {field}")
            
            print("\n🆕 NEW FIELDS IN SOURCE:")
            new_dev_fields = [
                "experience",
                "head_office_address",
                "branch_office_address",
                "company_size",
                "management_team",
                "key_service_and_specialities",
                "awards_and_recognition",
                "projects_in_top_cities"
            ]
            for field in new_dev_fields:
                print(f"  • {field}")
        
        # Analyze locations
        if data.get("locations"):
            print("\n🗺️  LOCATION SCHEMA MAPPING:")
            print("-" * 40)
            
            print("✅ MAPPED FIELDS:")
            mapped_loc_fields = [
                "id → projectLocationId",
                "location_name → location_name",
                "about_sector.overview → description",
                "indices → indices",
                "demand_supply → demand",
                "price_insights → price_insights"
            ]
            for field in mapped_loc_fields:
                print(f"  • {field}")
            
            print("\n🆕 NEW FIELDS IN SOURCE:")
            new_loc_fields = [
                "url",
                "image",
                "rank",
                "average_sale_price",
                "average_rental",
                "new_project_count",
                "properties_for_sale_count",
                "properties_for_rent_count",
                "neighbourhood"
            ]
            for field in new_loc_fields:
                print(f"  • {field}")
        
        print("\n" + "="*80)


def main():
    """Main execution function."""
    try:
        # Initialize importer
        importer = MongoDataImporter()
        
        # File path
        json_file = r"c:\Personal Drive\Project\Web-Data-Scraping\output\gurgaon_properties_with_local_assets.json"
        
        # Print mapping report
        importer.print_schema_mapping_report(json_file)
        
        # Import data
        results, dev_mapping, loc_mapping = importer.import_data(json_file)
        
        # Print foreign key summary
        importer.print_foreign_key_summary(dev_mapping, loc_mapping)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 IMPORT SUMMARY")
        print("="*60)
        print(f"Projects imported: {results['projects']}")
        print(f"Developers imported: {results['developers']}")
        print(f"Locations imported: {results['locations']}")
        print(f"Project Meta created: {results['project_meta']}")
        print(f"Errors encountered: {results['errors']}")
        print("="*60)
        
        if results['errors'] == 0:
            print("🎉 All data imported successfully!")
        else:
            print(f"⚠️  Import completed with {results['errors']} errors. Check logs above.")
            
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
