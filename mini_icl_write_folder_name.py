from creds import iclAPI, if_two_factor

#call the main function from creds.py - this is the function that handles 2fa
if_two_factor()

# List the contents of the 'Desktop' folder
desktop_contents = iclAPI.drive['Desktop'].dir()

# This will give you a list of all items (files and folders) in the 'Desktop' folder
print("Contents of Desktop folder:", desktop_contents)

# To further list contents of each subfolder in 'Desktop', you would iterate through the desktop_contents
for item in desktop_contents:
    try:
        # Attempt to list the contents of the item, assuming it might be a folder
        subfolder_contents = iclAPI.drive['Desktop'][item].dir()
        print(f"Contents of {item}:", subfolder_contents)
    except Exception as e:
        # If an error occurs, it's likely because the item is not a folder
        print(f"{item} is not a folder or could not be accessed. Error: {e}")
