#!/usr/bin/env python3
"""
Schema Mapping Report Generator
Shows how the JSON data maps to the provided MongoDB schemas without requiring MongoDB.
"""

import json
import re
from typing import Dict, List, Any, Optional


class SchemaMappingAnalyzer:
    """Analyzes how scraped data maps to MongoDB schemas."""
    
    def load_json_data(self, file_path: str) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"❌ Failed to load JSON file: {e}")
            raise
    
    def analyze_project_mapping(self, project: Dict[str, Any]):
        """Analyze how project data maps to ProjectDetailSchema."""
        print("\n🏗️  PROJECT SCHEMA MAPPING ANALYSIS")
        print("=" * 60)
        
        print("\n✅ DIRECT FIELD MAPPINGS:")
        direct_mappings = [
            ("property_id", "projectId", project.get("property_id")),
            ("location", "location/fullAddress", project.get("location")),
            ("about", "description", "✓ Available" if project.get("about") else "❌ Missing"),
            ("status", "propertyStatus", project.get("status")),
        ]
        
        for source, target, value in direct_mappings:
            status = "✓" if value else "❌"
            print(f"  {status} {source:20} → {target:25} | {str(value)[:50]}")
        
        print("\n✅ NESTED FIELD MAPPINGS:")
        nested_mappings = [
            ("builder_info.builder_id", "developerId", project.get("builder_info", {}).get("builder_id")),
            ("location_insights.location_id", "projectLocationId", project.get("location_insights", {}).get("location_id")),
        ]
        
        for source, target, value in nested_mappings:
            status = "✓" if value else "❌"
            print(f"  {status} {source:20} → {target:25} | {str(value)[:50]}")
        
        print("\n🔄 COMPLEX FIELD MAPPINGS:")
        complex_mappings = [
            ("information", "highlights", "✓ Converted to key-value pairs"),
            ("amenities", "amenities", "✓ Mapped to AmenityCategorySchema with categoryName, name, icon, status"),
            ("price_list", "priceList", "✓ Enhanced with floor plans"),
            ("thumbnail_image", "projectImages.coverImage", "✓ Added to images array"),
            ("floor_plans", "priceList.floorPlan", "✓ Integrated with price list"),
        ]
        
        for source, target, description in complex_mappings:
            print(f"  ✓ {source:20} → {target:25} | {description}")
        
        print("\n⚠️  MISSING IN SOURCE (Schema requires but not available):")
        missing_fields = [
            "lat/lng (coordinates)",
            "zipcode", 
            "propertyAge",
            "unitNo",
            "expectedPossession",
            "bathroom/balcony/parking (at project level)",
        ]
        for field in missing_fields:
            print(f"  ❌ {field}")
        
        print("\n🆕 ADDITIONAL FIELDS IN SOURCE (Not in schema but available):")
        additional_fields = [
            ("price_insights", "Rental supply, comparable projects data"),
            ("specifications", "Detailed building specifications"),
            ("nearby_landmarks", "Schools, hospitals, restaurants etc."),
            ("rera", "RERA registration details"),
            ("faq", "Frequently asked questions"),
            ("all_media", "Additional images and videos"),
        ]
        for field, description in additional_fields:
            print(f"  🆕 {field:20} | {description}")
    
    def analyze_developer_mapping(self, builder: Dict[str, Any]):
        """Analyze how builder data maps to developer schema."""
        print("\n👥 DEVELOPER SCHEMA MAPPING ANALYSIS")
        print("=" * 60)
        
        print("\n✅ DIRECT FIELD MAPPINGS:")
        direct_mappings = [
            ("id", "developerId", builder.get("id")),
            ("name", "name", builder.get("name")),
            ("overview", "description", "✓ Available" if builder.get("overview") else "❌ Missing"),
            ("customer_care_number", "customer_care_number", builder.get("customer_care_number")),
        ]
        
        for source, target, value in direct_mappings:
            status = "✓" if value else "❌"
            print(f"  {status} {source:20} → {target:25} | {str(value)[:50]}")
        
        print("\n✅ NESTED FIELD MAPPINGS:")
        nested_mappings = [
            ("image.src", "image", builder.get("image", {}).get("src")),
            ("projects", "projects", "✓ on_going, past, total available"),
        ]
        
        for source, target, value in nested_mappings:
            status = "✓" if value else "❌"
            print(f"  {status} {source:20} → {target:25} | {str(value)[:50]}")
        
        print("\n🔄 COMPLEX FIELD MAPPINGS:")
        complex_mappings = [
            ("faq", "faq", "✓ Array converted to JSON string"),
            ("key_service_and_specialities", "specialities", "✓ HTML converted to text"),
            ("awards_and_recognition", "awards", "✓ HTML converted to text"),
            ("company_size", "company_size", "✓ Number extracted from object"),
        ]
        
        for source, target, description in complex_mappings:
            print(f"  ✓ {source:20} → {target:25} | {description}")
        
        print("\n🆕 ADDITIONAL FIELDS IN SOURCE:")
        additional_fields = [
            ("experience", "Years of experience"),
            ("head_office_address", "Detailed office location"),
            ("branch_office_address", "Array of branch offices"),
            ("management_team", "CEO and team information"),
            ("projects_in_top_cities", "Projects by city"),
        ]
        for field, description in additional_fields:
            print(f"  🆕 {field:20} | {description}")
    
    def analyze_location_mapping(self, location: Dict[str, Any]):
        """Analyze how location data maps to location schema."""
        print("\n🗺️  LOCATION SCHEMA MAPPING ANALYSIS")
        print("=" * 60)
        
        print("\n✅ DIRECT FIELD MAPPINGS:")
        direct_mappings = [
            ("id", "projectLocationId", location.get("id")),
            ("location_name", "location_name", location.get("location_name")),
        ]
        
        for source, target, value in direct_mappings:
            status = "✓" if value else "❌"
            print(f"  {status} {source:20} → {target:25} | {str(value)[:50]}")
        
        print("\n✅ NESTED FIELD MAPPINGS:")
        nested_mappings = [
            ("about_sector.overview", "description", "✓ HTML converted to text"),
            ("indices", "indices", "✓ Array converted to heading/content/rating"),
            ("demand_supply", "demand", "✓ Sale data converted to by_property/bhk/budget"),
            ("price_insights", "price_insights", "✓ Direct mapping"),
        ]
        
        for source, target, description in nested_mappings:
            print(f"  ✓ {source:20} → {target:25} | {description}")
        
        print("\n🆕 ADDITIONAL FIELDS IN SOURCE:")
        additional_fields = [
            ("rank", "Locality ranking (e.g., 148 out of 542)"),
            ("average_sale_price", "Average price per sq ft"),
            ("average_rental", "Average rental per sq ft"),
            ("new_project_count", "Number of new projects"),
            ("properties_for_sale_count", "Available properties"),
            ("neighbourhood", "Nearby amenities with icons"),
            ("url", "Source URL for more details"),
        ]
        for field, description in additional_fields:
            print(f"  🆕 {field:20} | {description}")
    
    def analyze_meta_creation(self, projects: List[Dict], builders: List[Dict]):
        """Analyze project meta schema creation."""
        print("\n📊 PROJECT META SCHEMA ANALYSIS")
        print("=" * 60)
        
        # Analyze amenities
        amenity_categories = set()
        total_amenities = 0
        
        for project in projects:
            project_amenities = project.get("amenities", {})
            for category, items in project_amenities.items():
                amenity_categories.add(category)
                total_amenities += len(items)
        
        print(f"\n✅ AMENITIES EXTRACTION:")
        print(f"  • Total amenity categories: {len(amenity_categories)}")
        print(f"  • Categories found: {', '.join(sorted(amenity_categories))}")
        print(f"  • Total unique amenities: ~{total_amenities}")
        
        # Analyze bedrooms
        bedrooms = set()
        for project in projects:
            for price_item in project.get("price_list", []):
                unit_type = price_item.get("unit_type", "")
                match = re.search(r'(\d+)\s*BHK', unit_type, re.IGNORECASE)
                if match:
                    bedrooms.add(f"{match.group(1)} BHK")
        
        print(f"\n✅ BEDROOM CONFIGURATIONS:")
        print(f"  • Configurations found: {', '.join(sorted(bedrooms))}")
        
        # Analyze property statuses
        statuses = set()
        for project in projects:
            if project.get("status"):
                statuses.add(project["status"])
        
        print(f"\n✅ PROPERTY STATUSES:")
        print(f"  • Statuses found: {', '.join(sorted(statuses))}")
        
        print(f"\n🔄 META SCHEMA GENERATION:")
        meta_items = [
            ("propertyPurpose", "Inferred as 'Residential'"),
            ("buildingType", "Inferred as 'Apartment'"),
            ("propertyType", "Inferred as 'Project'"),
            ("bedrooms", f"Extracted from price lists: {len(bedrooms)} types"),
            ("propertyStatus", f"From project status: {len(statuses)} types"),
            ("amenities", f"From all projects: {len(amenity_categories)} categories"),
        ]
        
        for item, description in meta_items:
            print(f"  ✓ {item:20} | {description}")
    
    def generate_mapping_report(self, json_file_path: str):
        """Generate complete mapping report."""
        print("🚀 MONGODB SCHEMA MAPPING REPORT")
        print("=" * 80)
        print(f"📁 Source File: {json_file_path}")
        print("=" * 80)
        
        # Load data
        data = self.load_json_data(json_file_path)
        
        # Analyze each schema
        if data.get("projects"):
            self.analyze_project_mapping(data["projects"][0])
        
        if data.get("builders"):
            self.analyze_developer_mapping(data["builders"][0])
        
        if data.get("locations"):
            self.analyze_location_mapping(data["locations"][0])
        
        # Analyze meta creation
        self.analyze_meta_creation(data.get("projects", []), data.get("builders", []))
        
        # Summary statistics
        print(f"\n📈 DATA SUMMARY")
        print("=" * 60)
        print(f"Total Projects: {len(data.get('projects', []))}")
        print(f"Total Developers: {len(data.get('builders', []))}")
        print(f"Total Locations: {len(data.get('locations', []))}")
        
        print(f"\n💡 RECOMMENDATIONS")
        print("=" * 60)
        print("1. ✅ Most fields map successfully to the provided schemas")
        print("2. ⚠️  Some schema fields are missing in source data (coordinates, zipcode, etc.)")
        print("3. 🆕 Source data has many additional valuable fields not in schemas")
        print("4. 🔄 Complex data transformations are handled automatically")
        print("5. 📊 Project meta schema is generated from actual data")
        
        print(f"\n🎯 NEXT STEPS")
        print("=" * 60)
        print("1. Install MongoDB: pip install pymongo")
        print("2. Set up MongoDB connection")
        print("3. Run: python mongo_data_importer.py")
        print("4. Optionally extend schemas to include additional source fields")


def main():
    """Main execution function."""
    try:
        analyzer = SchemaMappingAnalyzer()
        json_file = r"c:\Personal Drive\Project\Web-Data-Scraping\output\gurgaon_properties_with_local_assets.json"
        analyzer.generate_mapping_report(json_file)
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
