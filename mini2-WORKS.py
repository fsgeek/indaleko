from creds import iclAPI, if_two_factor

#call the main function from creds.py - this is the function that handles 2fa
if_two_factor()

# List the contents of the 'Desktop' folder
desktop_contents = iclAPI.drive['Desktop'].dir()

# This will give you a list of all items (files and folders) in the 'Desktop' folder
#print("Contents of Desktop folder:", desktop_contents)

# Iterate through each item in the 'Desktop' folder
for item in desktop_contents:
    try:
        # Attempt to list the contents of the item, assuming it might be a folder
        subfolder_contents = iclAPI.drive['Desktop'][item].dir()
        if subfolder_contents is not None:
            print(f"Contents of folder '{item}':", subfolder_contents)
    except Exception as e:
        # Handle the error if needed (e.g., logging)
        pass  # Ignoring the error for now, since we're only interested in folders
