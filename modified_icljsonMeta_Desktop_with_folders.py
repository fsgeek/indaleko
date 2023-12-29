import uuid
import json
from creds import iclAPI, if_two_factor  # Importing the icliclAPI object from creds.py

#calling the main function from creds.py - this is the function that logs into iCloud
if_two_factor()

# Now you can proceed to interact with your iCloud account as authenticated


processed_folders = set()

def list_folder_contents(folder, path=''):
    """
    Recursively list the contents of a folder including subfolders.
    """
    items = folder.dir()
    folder_path = path.rsplit('/', 1)[0]
    if folder_path and folder_path not in processed_folders:
        # Add folder metadata
        folder_metadata = {
            'name': folder_path.rsplit('/', 1)[-1],
            'uuid': str(uuid.uuid4()),
            'path': folder_path,
            'type': 'folder'
        }
        files_metadata.append(folder_metadata)
        processed_folders.add(folder_path)
    
    for item_name in items:
        item = folder[item_name]
        item_path = f"{path}/{item_name}"

        if item.type == 'folder':
            # Recurse into the subfolder
            list_folder_contents(item, item_path)
        else:
            # Add file metadata
            metadata = {
                'uuid': str(uuid.uuid4()),
                'name': item.name,
                'size': item.size,
                'path': item_path,
                'created': item.date_modified.strftime('%Y-%m-%d %H:%M:%S') if item.date_modified else 'Unknown',
                'modified': item.date_modified.strftime('%Y-%m-%d %H:%M:%S') if item.date_modified else 'Unknown',
            }
            files_metadata.append(metadata)

# Ensure the json_output variable is defined.
json_output = '/'   # Replace with your desired path

# Get the root of the iCloud Drive
drive = iclAPI.drive

# Initialize the metadata list
files_metadata = []

# Check if 'Desktop' folder exists and list its contents
if 'Desktop' in drive.dir():
    desktop_folder = drive['Desktop']
    list_folder_contents(desktop_folder)
else:
    print("The 'Desktop' folder was not found in your iCloud Drive.")

# Write the file names and metadata to a JSON file
with open(json_output, 'w', encoding='utf-8') as jsonfile:
    json.dump(files_metadata, jsonfile, ensure_ascii=False, indent=4)

print(f"Index of files and their metadata has been saved to {json_output}")
