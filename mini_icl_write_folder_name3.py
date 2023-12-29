from creds import iclAPI, if_two_factor

#call the main function from creds.py - this is the function that handles 2fa
if_two_factor()

# List the contents of the 'Desktop' folder
desktop_contents = iclAPI.drive['Desktop'].dir()



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
