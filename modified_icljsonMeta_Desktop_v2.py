
import sys
import json
import uuid
from creds import iclAPI, if_two_factor  # Importing the iclAPI object from creds.py

#calling the main function from creds.py - this is the function that logs into iCloud
if_two_factor()

# List the contents of the 'Desktop' folder
desktop_contents = iclAPI.drive['Desktop'].dir()

# Function to check if an item is a folder
def check_any_subfolders() -> bool:
    """
    Recursively list the contents of a folder including subfolders.
    """
    for item in desktop_contents:
        try:
            # Attempt to list the contents of the item, assuming it might be a folder
            subfolder_contents = iclAPI.drive['Desktop'][item].dir()
            if subfolder_contents is not None:
                return True
            else:
                return False
        except Exception as e:
            # Handle the error if needed (e.g., logging)
            pass  # Ignoring the error for now, since we're only interested in folders


# Function to recursively list contents of a folder and record folder names
def list_folder_contents(iclAPI, folder_path, base_path=''):
    items = iclAPI.drive[folder_path].dir()
    for item_name in items:
        item_path = f"{base_path}/{item_name}" if base_path else item_name
        if check_any_subfolders():
            # It's a folder, add its metadata and recurse
            folder_metadata = {
                'name': item_name,
                'uuid': str(uuid.uuid4()),
                'path': item_path,
                'type': 'folder'
            }
            files_metadata.append(folder_metadata)
            list_folder_contents(iclAPI, item_path, item_path)
        else:
            # It's a file, add its metadata
            file_metadata = {
                'name': item_name,
                'uuid': str(uuid.uuid4()),
                'path': item_path,
                'type': 'file'
            }
            files_metadata.append(file_metadata)

# Ensure the json_output variable is defined.
json_output = '/'  # Replace with your desired output path

# Initialize the metadata list
files_metadata = []

# Check if 'Desktop' folder exists and list its contents
if 'Desktop' in iclAPI.drive.dir():
    list_folder_contents(iclAPI, 'Desktop')
else:
    print("The 'Desktop' folder was not found in your iCloud Drive.")

# Write the file and folder names and metadata to a JSON file
with open(json_output, 'w', encoding='utf-8') as jsonfile:
    json.dump(files_metadata, jsonfile, ensure_ascii=False, indent=4)

print(f"Index of files and folders and their metadata has been saved to {json_output}")
