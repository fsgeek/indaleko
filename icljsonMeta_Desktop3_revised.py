
import json
from creds import iclAPI, if_two_factor  # Importing the iclAPI object and if_two_factor from creds.py

# Authenticate with iCloud using if_two_factor function
if_two_factor()

def list_folder_contents(folder, path=''):
    """
    Recursively list the contents of a folder. 
    If an item is a folder (determined by its ability to list contents), 
    it recursively lists the contents of that folder.
    """
    items = folder.dir()
    for item_name in items:
        item = folder[item_name]
        print(f"{'/' + path if path else ''}/{item_name}")
        try:
            # Attempt to list the contents of the item
            if item.dir():
                # If successful, recurse into this folder
                list_folder_contents(item, path=path + '/' + item_name)
        except Exception as e:
            # If the item is not a folder, it will raise an exception which we ignore
            pass

# List and print the contents of the 'Desktop' folder recursively
desktop_folder = iclAPI.drive['Desktop']
list_folder_contents(desktop_folder)
