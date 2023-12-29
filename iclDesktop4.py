from creds import iclAPI, if_two_factor  # Importing the iclAPI object and if_two_factor from creds.py

# Authenticate with iCloud using if_two_factor function
if_two_factor()

def list_folder_contents(folder, path='', folder_dict=None):
    """
    Recursively list the contents of a folder and record folder paths in a dictionary. 
    """
    if folder_dict is None:
        folder_dict = {}

    items = folder.dir()
    for item_name in items:
        item = folder[item_name]
        item_path = f"{path}/{item_name}" if path else item_name
        try:
            # If the item is a folder, add it to the dictionary and recurse into it
            if item.dir():
                folder_dict[item_name] = item_path
                list_folder_contents(item, item_path, folder_dict)
        except Exception as e:
            # If the item is not a folder, it will raise an exception which we ignore
            pass

    return folder_dict

# List and record the contents of the 'Desktop' folder recursively
desktop = iclAPI.drive['Desktop']
folders_dict = list_folder_contents(desktop)
print("Folders and their paths:", folders_dict)
