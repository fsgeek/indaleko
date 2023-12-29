
from creds import iclAPI, if_two_factor
import json

#calling the main function from creds.py - this is the function that logs into iCloud
if_two_factor()

# Function to get the metadata of top-level files
def list_top_level_contents(drive):
    """
    List the contents of the top level of the iCloud Drive.
    """
    items = drive.dir()  # Get all items at the top level
    for item_name in items:
        item = drive[item_name]
        if item.type == 'file':  # Only add metadata for files
            metadata = {
                'name': item.name,
                'size': item.size,
                'path': f"/{item_name}",
                'modified': item.date_modified.strftime('%Y-%m-%d %H:%M:%S') if item.date_modified else 'Unknown'
            }
            files_metadata.append(metadata)

# Ensure the json_output variable is defined
json_output = '/Users/zeethompson/wRes/indaleko-scan_contents_of_icloud-test/icl_top_level_meta.json'  # Replace with your desired path

# Get the root of the iCloud Drive
drive = iclAPI.drive

# Initialize the metadata list
files_metadata = []

# List the contents of the top level
list_top_level_contents(drive)

# Write the file names and metadata to a JSON file
with open(json_output, 'w', encoding='utf-8') as jsonfile:
    json.dump(files_metadata, jsonfile, ensure_ascii=False, indent=4)

print(f"Index of files and their metadata has been saved to {json_output}")
