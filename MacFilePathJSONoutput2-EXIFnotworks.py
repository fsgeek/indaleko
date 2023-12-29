import os
import json
import datetime
from PIL import Image
from PIL.ExifTags import TAGS

def rational_to_string(rational):
    return f"{rational.numerator}/{rational.denominator}"

def get_exif_data(file_path):
    try:
        image = Image.open(file_path)
        exif_data = {}
        exif_info = image._getexif()
        if exif_info is not None:
            for tag, value in exif_info.items():
                decoded_tag = TAGS.get(tag, tag)
                if isinstance(value, bytes):
                    value = value.decode(errors='ignore')  # decode bytes to string
                elif isinstance(value, Image.Image):  # for 'thumbnail' data
                    value = '<Image data>'
                elif isinstance(value, Image.Exif):
                    value = '<Exif data>'
                elif isinstance(value, tuple) and all(isinstance(x, Image.IFDRational) for x in value):
                    # Convert all IFDRational objects in the tuple to strings
                    value = tuple(rational_to_string(x) if isinstance(x, Image.IFDRational) else x for x in value)
                elif isinstance(value, Image.IFDRational):
                    # Convert individual IFDRational object to string
                    value = rational_to_string(value)
                elif not isinstance(value, (int, float, str, list, dict, tuple)):
                    value = str(value)  # convert other non-serializable types to string
                exif_data[decoded_tag] = value
        return exif_data
    except Exception as e:
        print(f"Could not get EXIF data for file: {file_path}. Error: {e}")
        return {}


def get_file_metadata(file_path):
    try:
        stats = os.stat(file_path)
        created_time = datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified_time = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        metadata = {
            'size': stats.st_size,
            'created': created_time,
            'modified': modified_time,
        }
        
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            exif_data = get_exif_data(file_path)
            if exif_data:
                metadata['exif'] = exif_data
        
        return metadata
    except Exception as e:
        print(f"Could not get metadata for file: {file_path}. Error: {e}")
        return {}

def index_directory(path, json_output, parent_path=""):
    files_metadata = []
    
    # Get all entries in the directory
    for entry in os.scandir(path):
        if entry.is_dir():
            # Recursively index subdirectories
            subfolder_metadata = index_directory(entry.path, json_output, os.path.join(parent_path, entry.name))
            files_metadata.extend(subfolder_metadata)
        elif entry.is_file():
            file_path = entry.path
            metadata = get_file_metadata(file_path)
            metadata['name'] = entry.name
            metadata['path'] = os.path.join(parent_path, entry.name)
            files_metadata.append(metadata)
    
    return files_metadata

def write_to_json(data, json_output):
    with open(json_output, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=4)

# Example usage:

# folder_path = '/path/to/your/folder'
json_output = 'output-02.json'
metadata = index_directory(folder_path, json_output)
write_to_json(metadata, json_output)
print(f"Index of files and their metadata has been saved to {json_output}")
