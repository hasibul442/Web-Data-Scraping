import os
import sys
import json
import requests
from urllib.parse import urlparse
from tqdm import tqdm
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to Python path when run directly
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, os.path.join(project_root, 'src'))

from core.config import MAX_WORKERS

# === Custom Paths ===
# Get project root directory
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
else:
    # When imported as module, get root differently
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INPUT_JSON = os.path.join(project_root, "output", "gurgaon_properties.json")
OUTPUT_JSON = os.path.join(project_root, "output", "gurgaon_properties_with_local_assets.json")
ASSETS_ROOT = os.path.join(project_root, "output") + os.sep
LOG_FILE = os.path.join(project_root, "output", "download_log.txt")

# Thread-safe download log with lock
download_log_lock = threading.Lock()
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
    """Download file from URL to full_path if it doesn't exist. Thread-safe."""
    if os.path.exists(full_path):
        with download_log_lock:
            download_log["skipped"].append(full_path)
        return True
    
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            with download_log_lock:
                download_log["downloaded"].append(full_path)
            return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        with download_log_lock:
            download_log["failed"].append((url, full_path))
    return False

def get_asset_relative_path(base, *parts):
    """Construct relative asset path."""
    path_parts = [base] + [sanitize_folder(part) for part in parts]
    return os.path.join(*path_parts).replace("\\", "/")

def get_full_local_path(relative_asset_path):
    """Get full local path for asset."""
    return os.path.join(ASSETS_ROOT, relative_asset_path).replace("\\", "/")

def download_asset_concurrent(asset_info):
    """Helper function to download a single asset concurrently."""
    url, rel_path = asset_info
    full_path = get_full_local_path(rel_path)
    success = download_if_needed(url, full_path)
    return (success, rel_path)

def process_assets_concurrently(asset_list, max_workers=None):
    """Process multiple assets concurrently and return successful paths."""
    if not asset_list:
        return {}
    
    if max_workers is None:
        max_workers = min(MAX_WORKERS, len(asset_list))
    
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {executor.submit(download_asset_concurrent, asset_info): key 
                        for key, asset_info in asset_list.items()}
        
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                success, rel_path = future.result()
                if success:
                    results[key] = rel_path
            except Exception as e:
                print(f"Error downloading asset {key}: {e}")
    
    return results

def replace_and_download_project(project):
    """Process project assets and download them with optimized concurrent downloading."""
    property_id = project.get("property_id", "unknown")
    project_name = project.get("name", "unknown")
    project_folder = f"assets/projects/{sanitize_folder(project_name)}_{property_id}"

    # Collect all download tasks
    download_tasks = {}

    # === Thumbnail Image ===
    if "thumbnail_image" in project:
        url = project["thumbnail_image"]
        filename = os.path.basename(urlparse(url).path)
        filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
        rel_path = get_asset_relative_path(project_folder, "thumbnail", filename)
        download_tasks["thumbnail_image"] = (url, rel_path)

    # === Amenities Icons (process immediately due to shared nature) ===
    amenities = project.get("amenities", {})
    if amenities:
        for category, items in amenities.items():
            if items:  # Check if items is not None
                for item in items:
                    if item and "icon" in item:
                        url = item["icon"]
                        filename = os.path.basename(urlparse(url).path)
                        filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                        rel_path = get_asset_relative_path("assets/projects/common/amenities", category, filename)
                        full_path = get_full_local_path(rel_path)
                        if download_if_needed(url, full_path):
                            item["icon"] = rel_path

    # === Floor Plan Images ===
    floor_plan_tasks = {}
    floor_plan_mapping = {}
    floor_plans = project.get("floor_plans", {})
    if floor_plans:
        for plan_type, items in floor_plans.items():
            if items:  # Check if items is not None
                for i, item in enumerate(items):
                    if item and "2d_src" in item and item["2d_src"]:
                        url = item["2d_src"]
                        filename = os.path.basename(urlparse(url).path)
                        filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                        rel_path = get_asset_relative_path(project_folder, "floor_plan_image", plan_type, filename)
                        task_key = f"floor_plan_{plan_type}_{i}"
                        floor_plan_tasks[task_key] = (url, rel_path)
                        floor_plan_mapping[task_key] = (plan_type, i, "2d_src")

    # === All Media Images ===
    media_tasks = {}
    media_mapping = {}
    all_media = project.get("all_media", {})
    if all_media:
        all_images = all_media.get("images", {})
        if all_images:
            for section, items in all_images.items():
                if items:  # Check if items is not None
                    for i, img in enumerate(items):
                        if img and "src" in img:
                            url = img["src"]
                            filename = os.path.basename(urlparse(url).path)
                            filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                            rel_path = get_asset_relative_path(project_folder, "images", section, filename)
                            task_key = f"media_{section}_{i}"
                            media_tasks[task_key] = (url, rel_path)
                            media_mapping[task_key] = (section, i, "src")

    # === All Media Videos ===
    video_tasks = {}
    video_mapping = {}
    if all_media:
        all_videos = all_media.get("videos", [])
        if all_videos:
            for i, vid in enumerate(all_videos):
                if vid and "src" in vid and vid["src"] and vid["src"].startswith("http"):
                    url = vid["src"]
                    filename = os.path.basename(urlparse(url).path)
                    filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                    rel_path = get_asset_relative_path(project_folder, "videos", filename)
                    task_key = f"video_{i}"
                    video_tasks[task_key] = (url, rel_path)
                    video_mapping[task_key] = (i, "src")

    # === Builder Info Assets ===
    builder_info = project.get("builder_info", {})
    if builder_info and "image" in builder_info and builder_info["image"] and builder_info["image"].startswith("http"):
        url = builder_info["image"]
        filename = os.path.basename(urlparse(url).path)
        filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
        rel_path = get_asset_relative_path(project_folder, "builder_info", "logo", filename)
        download_tasks["builder_info_image"] = (url, rel_path)

    # === Location Insights Assets ===
    location_insights = project.get("location_insights", {})
    location_insight_tasks = {}
    location_insight_mapping = {}
    if location_insights and "insights" in location_insights:
        insights = location_insights["insights"]
        if insights:  # Check if insights is not None
            for i, insight in enumerate(insights):
                if insight and "icon" in insight and insight["icon"] and insight["icon"].startswith("http"):
                    url = insight["icon"]
                    filename = os.path.basename(urlparse(url).path)
                    filename = f"{os.path.splitext(filename)[0]}{get_file_extension(url)}"
                    rel_path = get_asset_relative_path(project_folder, "location_insights", "icons", filename)
                    task_key = f"location_insight_{i}"
                    location_insight_tasks[task_key] = (url, rel_path)
                    location_insight_mapping[task_key] = i

    # Process all download tasks concurrently
    all_tasks = {**download_tasks, **floor_plan_tasks, **media_tasks, **video_tasks, **location_insight_tasks}
    
    if all_tasks:
        successful_downloads = process_assets_concurrently(all_tasks, max_workers=min(MAX_WORKERS, len(all_tasks)))
        
        # Update project with successful download paths
        if "thumbnail_image" in successful_downloads:
            project["thumbnail_image"] = successful_downloads["thumbnail_image"]
        
        if "builder_info_image" in successful_downloads:
            builder_info["image"] = successful_downloads["builder_info_image"]
        
        # Update floor plans
        for task_key, rel_path in successful_downloads.items():
            if task_key in floor_plan_mapping:
                plan_type, item_index, field = floor_plan_mapping[task_key]
                if "floor_plans" in project and project["floor_plans"] and plan_type in project["floor_plans"]:
                    if project["floor_plans"][plan_type] and item_index < len(project["floor_plans"][plan_type]):
                        project["floor_plans"][plan_type][item_index][field] = rel_path
        
        # Update media images
        for task_key, rel_path in successful_downloads.items():
            if task_key in media_mapping:
                section, item_index, field = media_mapping[task_key]
                if ("all_media" in project and project["all_media"] and 
                    "images" in project["all_media"] and project["all_media"]["images"] and
                    section in project["all_media"]["images"] and project["all_media"]["images"][section] and
                    item_index < len(project["all_media"]["images"][section])):
                    project["all_media"]["images"][section][item_index][field] = rel_path
        
        # Update media videos
        for task_key, rel_path in successful_downloads.items():
            if task_key in video_mapping:
                item_index, field = video_mapping[task_key]
                if ("all_media" in project and project["all_media"] and 
                    "videos" in project["all_media"] and project["all_media"]["videos"] and
                    item_index < len(project["all_media"]["videos"])):
                    project["all_media"]["videos"][item_index][field] = rel_path
        
        # Update location insights
        for task_key, rel_path in successful_downloads.items():
            if task_key in location_insight_mapping:
                insight_index = location_insight_mapping[task_key]
                if ("location_insights" in project and project["location_insights"] and
                    "insights" in project["location_insights"] and project["location_insights"]["insights"] and
                    insight_index < len(project["location_insights"]["insights"])):
                    project["location_insights"]["insights"][insight_index]["icon"] = rel_path

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
    """Main function to process JSON and download assets with multi-threading."""
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Starting asset processing with {MAX_WORKERS} threads...")
    
    # Process projects with multi-threading
    updated_projects = []
    projects = data.get("projects", [])
    if projects:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all project processing tasks
            project_futures = {executor.submit(replace_and_download_project, project): project 
                             for project in projects}
            
            # Process completed tasks with progress bar
            for future in tqdm(as_completed(project_futures), 
                             total=len(project_futures), 
                             desc="Processing Projects"):
                try:
                    updated_project = future.result()
                    updated_projects.append(updated_project)
                except Exception as e:
                    project = project_futures[future]
                    print(f"Error processing project {project.get('name', 'Unknown')}: {e}")
                    updated_projects.append(project)  # Keep original if processing fails

    # Process builders with multi-threading
    updated_builders = []
    builders = data.get("builders", [])
    if builders:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all builder processing tasks
            builder_futures = {executor.submit(replace_and_download_builder, builder): builder 
                             for builder in builders}
            
            # Process completed tasks with progress bar
            for future in tqdm(as_completed(builder_futures), 
                             total=len(builder_futures), 
                             desc="Processing Builders"):
                try:
                    updated_builder = future.result()
                    updated_builders.append(updated_builder)
                except Exception as e:
                    builder = builder_futures[future]
                    print(f"Error processing builder {builder.get('name', 'Unknown')}: {e}")
                    updated_builders.append(builder)  # Keep original if processing fails

    # Process locations with multi-threading
    updated_locations = []
    locations = data.get("locations", [])
    if locations:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all location processing tasks
            location_futures = {executor.submit(replace_and_download_location, location): location 
                              for location in locations}
            
            # Process completed tasks with progress bar
            for future in tqdm(as_completed(location_futures), 
                             total=len(location_futures), 
                             desc="Processing Locations"):
                try:
                    updated_location = future.result()
                    updated_locations.append(updated_location)
                except Exception as e:
                    location = location_futures[future]
                    print(f"Error processing location {location.get('name', 'Unknown')}: {e}")
                    updated_locations.append(location)  # Keep original if processing fails

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
    
    # Print summary
    with download_log_lock:
        total_downloaded = len(download_log["downloaded"])
        total_skipped = len(download_log["skipped"])
        total_failed = len(download_log["failed"])
    
    print(f"\n✅ JSON updated: {OUTPUT_JSON}")
    print(f"📄 Download log: {LOG_FILE}")
    print(f"📊 Summary: {total_downloaded} downloaded, {total_skipped} skipped, {total_failed} failed")
    print(f"🧵 Processing completed using {MAX_WORKERS} threads")

if __name__ == "__main__":
    main()