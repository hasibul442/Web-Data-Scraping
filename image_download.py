import os
import json
import requests
from urllib.parse import urlparse
from tqdm import tqdm

# === Custom Paths ===
INPUT_JSON = "output/gurgaon_properties.json"
OUTPUT_JSON = "output/gurgaon_properties_with_local_assets.json"
ASSETS_ROOT = "output/assets"
LOG_FILE = "output/download_log.txt"

download_log = {
    "downloaded": [],
    "skipped": [],
    "failed": []
}

def sanitize_folder(name):
    return name.strip().replace(" ", "_")

def download_if_needed(url, full_path):
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

def get_asset_relative_path(property_id, category, filename, subfolder=None):
    path_parts = ["assets", property_id, sanitize_folder(category)]
    if subfolder:
        path_parts.append(sanitize_folder(subfolder))
    path_parts.append(filename)
    return os.path.join(*path_parts).replace("\\", "/")

def get_full_local_path(relative_asset_path):
    return os.path.join("output", relative_asset_path).replace("\\", "/")

def replace_and_download(obj):
    property_id = obj.get("property_id", "unknown")

    # === Builder Logo ===
    if "builder_info" in obj and "image" in obj["builder_info"]:
        url = obj["builder_info"]["image"]
        filename = os.path.basename(urlparse(url).path)
        rel_path = get_asset_relative_path(property_id, "Builder Logo", filename)
        full_path = get_full_local_path(rel_path)
        if download_if_needed(url, full_path):
            obj["builder_info"]["image"] = rel_path

    # === Thumbnail Image ===
    project = obj.get("project", {})
    if "thumbnail_image" in project:
        url = project["thumbnail_image"]
        filename = os.path.basename(urlparse(url).path)
        rel_path = get_asset_relative_path(property_id, "Project Images/Thumbnail", filename)
        full_path = get_full_local_path(rel_path)
        if download_if_needed(url, full_path):
            project["thumbnail_image"] = rel_path

    # === Amenities Icons ===
    for category, items in project.get("amenities", {}).items():
        for item in items:
            if "icon" in item:
                url = item["icon"]
                filename = os.path.basename(urlparse(url).path)
                rel_path = get_asset_relative_path(property_id, "Amenities Icon", filename)
                full_path = get_full_local_path(rel_path)
                if download_if_needed(url, full_path):
                    item["icon"] = rel_path

    # === Floor Plan Images ===
    for plan_type, items in project.get("floor_plans", {}).items():
        for item in items:
            # 2D source: replace & download
            if "2d_src" in item and item["2d_src"]:
                url = item["2d_src"]
                filename = os.path.basename(urlparse(url).path)
                rel_path = get_asset_relative_path(property_id, "Floor Plan Image", filename, subfolder=plan_type)
                full_path = get_full_local_path(rel_path)
                if download_if_needed(url, full_path):
                    item["2d_src"] = rel_path
            # 3D source: keep as is

    # === all_media.images ===
    all_images = obj.get("all_media", {}).get("images", {})
    for section, items in all_images.items():
        for img in items:
            if "src" in img:
                url = img["src"]
                filename = os.path.basename(urlparse(url).path)
                rel_path = get_asset_relative_path(property_id, f"Project Images/{section}", filename)
                full_path = get_full_local_path(rel_path)
                if download_if_needed(url, full_path):
                    img["src"] = rel_path

    # === all_media.videos ===
    all_videos = obj.get("all_media", {}).get("videos", [])
    for vid in all_videos:
        if "src" in vid and vid["src"].startswith("http"):
            url = vid["src"]
            filename = os.path.basename(urlparse(url).path)
            rel_path = get_asset_relative_path(property_id, "Videos", filename)
            full_path = get_full_local_path(rel_path)
            if download_if_needed(url, full_path):
                vid["src"] = rel_path

    return obj

def write_log():
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
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated_data = []
    for prop in tqdm(data, desc="Processing Properties"):
        updated_data.append(replace_and_download(prop))

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    write_log()
    print(f"\n✅ JSON updated: {OUTPUT_JSON}")
    print(f"📄 Download log: {LOG_FILE}")

if __name__ == "__main__":
    main()
