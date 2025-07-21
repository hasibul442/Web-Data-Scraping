import os
import json
import requests
from urllib.parse import urlparse
from tqdm import tqdm
import re

# === Custom Paths ===
INPUT_JSON = "output/gurgaon_properties.json"
OUTPUT_JSON = "output/gurgaon_properties_with_local_assets.json"
ASSETS_ROOT = "output/"
LOG_FILE = "output/download_log.txt"

download_log = {
    "downloaded": [],
    "skipped": [],
    "failed": []
}

def sanitize_folder(name):
    """Sanitize folder name by replacing spaces and special characters."""
    return re.sub(r'[^a-zA-Z0-9\.]', '_', name.strip())

def get_file_extension(url):
    """Extract the correct file extension from the URL."""
    parsed = urlparse(url)
    path = parsed.path
    return os.path.splitext(path)[1] or '.jpg'  # Default to .jpg if no extension

def download_if_needed(url, full_path):
    """Download file from URL to full_path if it doesn't exist."""
    if os.path.exists(full_path):
        download_log["skipped"].append(full_path)
        return True
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            download_log["downloaded"].append(full_path)
            return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        download_log["failed"].append((url, full_path))
    return False

def get_asset_relative_path(base, *parts):
    """Construct relative asset path."""
    path_parts = [base] + [sanitize_folder(part) for part in parts]
    return os.path.join(*path_parts).replace("\\", "/")

def get_full_local_path(relative_asset_path):
    """Get full local path for asset."""
    return os.path.join(ASSETS_ROOT, relative_asset_path).replace("\\", "/")

def replace_and_download_project(project):
    """Process project assets and download them."""
    property_id = project.get("property_id", "unknown")
    project_name = project.get("name", "unknown")
    project_folder = f"assets/projects/{sanitize_folder(project_name)}_{property_id}"

    # === Thumbnail Image ===
    if "thumbnail_image" in project:
        url = project["thumbnail_image"]
        filename = os.path.basename(urlparse(url).path)
        filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
        rel_path = get_asset_relative_path(project_folder, "Thumbnail", filename)
        full_path = get_full_local_path(rel_path)
        if download_if_needed(url, full_path):
            project["thumbnail_image"] = rel_path

    # === Amenities Icons ===
    for category, items in project.get("amenities", {}).items():
        for item in items:
            if "icon" in item:
                url = item["icon"]
                filename = os.path.basename(urlparse(url).path)
                filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                rel_path = get_asset_relative_path("assets/projects/common/amenities", category, filename)
                full_path = get_full_local_path(rel_path)
                if download_if_needed(url, full_path):
                    item["icon"] = rel_path

    # === Floor Plan Images ===
    for plan_type, items in project.get("floor_plans", {}).items():
        for item in items:
            if "2d_src" in item and item["2d_src"]:
                url = item["2d_src"]
                filename = os.path.basename(urlparse(url).path)
                filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                rel_path = get_asset_relative_path(project_folder, "Floor_Plan_Image", plan_type, filename)
                full_path = get_full_local_path(rel_path)
                if download_if_needed(url, full_path):
                    item["2d_src"] = rel_path

    # === All Media Images ===
    all_images = project.get("all_media", {}).get("images", {})
    for section, items in all_images.items():
        for img in items:
            if "src" in img:
                url = img["src"]
                filename = os.path.basename(urlparse(url).path)
                filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                rel_path = get_asset_relative_path(project_folder, "Images", section, filename)
                full_path = get_full_local_path(rel_path)
                if download_if_needed(url, full_path):
                    img["src"] = rel_path

    # === All Media Videos ===
    all_videos = project.get("all_media", {}).get("videos", [])
    for vid in all_videos:
        if "src" in vid and vid["src"].startswith("http"):
            url = vid["src"]
            filename = os.path.basename(urlparse(url).path)
            filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
            rel_path = get_asset_relative_path(project_folder, "Videos", filename)
            full_path = get_full_local_path(rel_path)
            if download_if_needed(url, full_path):
                vid["src"] = rel_path

    return project

def replace_and_download_builder(builder):
    """Process builder assets and download them."""
    builder_id = builder.get("id", "unknown")
    builder_name = builder.get("name", "unknown")
    builder_folder = f"assets/builders/{sanitize_folder(builder_name)}_{builder_id}"

    # === Builder Logo ===
    if "image" in builder and isinstance(builder["image"], dict) and "src" in builder["image"]:
        url = builder["image"]["src"]
        filename = os.path.basename(urlparse(url).path)
        filename = f"{os.path.splitext(filename)[0]}"
        filename += get_file_extension(url)
        rel_path = get_asset_relative_path(builder_folder, "logo", filename)
        full_path = get_full_local_path(rel_path)
        if download_if_needed(url, full_path):
            builder["image"]["src"] = rel_path

    # === Management Team Images ===
    for team_category, members in builder.get("management_team", {}).items():
        for member in members:
            if "image" in member and member["image"]:
                url = member["image"]
                filename = os.path.basename(urlparse(url).path)
                filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                rel_path = get_asset_relative_path(builder_folder, "team", filename)
                full_path = get_full_local_path(rel_path)
                if download_if_needed(url, full_path):
                    member["image"] = rel_path

    return builder

def replace_and_download_location(location):
    """Process location assets and download them."""
    location_id = location.get("id", "unknown")
    location_name = location.get("location_name", "unknown")
    location_folder = f"assets/locations/{sanitize_folder(location_name)}_{location_id}"

    # === Location Image ===
    if "image" in location:
        url = location["image"]
        filename = os.path.basename(urlparse(url).path)
        filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
        rel_path = get_asset_relative_path(location_folder, "location_image", filename)
        full_path = get_full_local_path(rel_path)
        if download_if_needed(url, full_path):
            location["image"] = rel_path

    # === Neighbourhood Icons ===
    for neighbour in location.get("neighbourhood", []):
        if "icon" in neighbour:
            url = neighbour["icon"]
            filename = os.path.basename(urlparse(url).path)
            filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
            rel_path = get_asset_relative_path(location_folder, "neighbourhood", filename)
            full_path = get_full_local_path(rel_path)
            if download_if_needed(url, full_path):
                neighbour["icon"] = rel_path

    return location

def write_log():
    """Write download log to file."""
    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write("==== Downloaded Files ====\n")
        for path in download_log["downloaded"]:
            log.write(f"Downloaded: {path}\n")
        log.write("\n==== Skipped Files (Already Exists) ====\n")
        for path in download_log["skipped"]:
            log.write(f"Skipped: {path}\n")
        log.write("\n==== Failed Downloads ====\n")
        for url, path in download_log["failed"]:
            log.write(f"Failed: {url} -> {path}\n")

def main():
    """Main function to process JSON and download assets."""
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Process projects
    updated_projects = []
    for project in tqdm(data.get("projects", []), desc="Processing Projects"):
        updated_projects.append(replace_and_download_project(project))

    # Process builders
    updated_builders = []
    for builder in tqdm(data.get("builders", []), desc="Processing Builders"):
        updated_builders.append(replace_and_download_builder(builder))

    # Process locations
    updated_locations = []
    for location in tqdm(data.get("locations", []), desc="Processing Locations"):
        updated_locations.append(replace_and_download_location(location))

    # Update the data
    updated_data = {
        "projects": updated_projects,
        "builders": updated_builders,
        "locations": updated_locations
    }

    # Write updated JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    # Write log
    write_log()
    print(f"\n✅ JSON updated: {OUTPUT_JSON}")
    print(f"📄 Download log: {LOG_FILE}")

if __name__ == "__main__":
    main()