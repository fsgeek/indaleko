import sys
from creds import iclAPI  # Importing the iclAPI object from creds.py
import json


def handle_two_factor():
    if iclAPI.requires_2fa:     # Check if two-factor authentication (2FA) is required
        print("Two-factor authentication required.")
        # Prompt the user to enter the code they received on their trusted device
        code = input("Enter the code you received of one of your approved devices: ")
        # Validate the entered 2FA code
        result = iclAPI.validate_2fa_code(code)
        print("Code validation result: %s" % result)

        if not result:
            print("Failed to verify security code")
            sys.exit(1)  # Exit if the 2FA code validation fails

        if not iclAPI.is_trusted_session:
            print("Session is not trusted. Requesting trust...")
            result = iclAPI.trust_session()
            print("Session trust result %s" % result)

            if not result:
                print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
    elif iclAPI.requires_2sa: # If the account has two-step authentication (2SA) enabled
        import click
        print("Two-step authentication required. Your trusted devices are:")

        # List the trusted devices associated with the iCloud account
        devices = iclAPI.trusted_devices
        for i, device in enumerate(devices):
            print(
                "  %s: %s" % (i, device.get('deviceName',
                "SMS to %s" % device.get('phoneNumber')))
            )

        # Prompt the user to select one of the devices to receive a verification code
        device = click.prompt('Which device would you like to use?', default=0)
        device = devices[device]
        if not iclAPI.send_verification_code(device):
            print("Failed to send verification code")
            sys.exit(1)  # Exit if sending the verification code fails

        # Prompt the user to enter the received verification code
        code = click.prompt('Please enter validation code')
        if not iclAPI.validate_verification_code(device, code):
            print("Failed to verify verification code")
            sys.exit(1)  # Exit if the verification code validation fails

    # If no additional authentication is needed, print a success message
    else:
        print("Logged in successfully.")



# # Now let's try to list the Account devices
# print("Listing devices associated with the account...")

# devices = iclAPI.devices
# for device_id, device in devices.items():
#     print(f"Device ID: {device_id}")
#     print(f"  Device Name: {device.data['name']}")
#     print(f"  Device Model: {device.data['modelDisplayName']}")
#     print(f"  Device Status: {device.data['deviceStatus']}")
#     print(f"  Battery Level: {device.data.get('batteryLevel', 'Unknown')}")

def get_folder_contents(folder, drive, path=''):
    """
    Recursively get the contents of a folder and return a list of file metadata.
    """
    items_metadata = []
    for item_name in folder.dir():
        item = folder[item_name]
        item_path = f"{path}/{item_name}"

        if item.type == 'folder':
            # Recursively get the contents of this folder
            items_metadata.extend(get_folder_contents(item, drive, item_path))
        else:
            metadata = {
                'name': item.name,
                'path': item_path,
                'size': item.size,
                'created': item.date_modified.strftime('%Y-%m-%d %H:%M:%S') if item.date_modified else 'Unknown',
                'modified': item.date_modified.strftime('%Y-%m-%d %H:%M:%S') if item.date_modified else 'Unknown'
            }
            items_metadata.append(metadata)
    
    return items_metadata

def index_to_json():
    json_output = '/Users/.../'  # Ensure this is a file path to a file not a folder. Make a name...I am withopen() in write mode so the file will becreated if there isn't already a file.

    # Get the root of the iCloud Drive
    drive = iclAPI.drive
    root_folder = drive.root  # Access it as a property, not a method

    # Recursively get all files metadata starting from the root
    files_metadata = get_folder_contents(root_folder, drive)

    # Write the file names and metadata to a JSON file
    with open(json_output, 'w', encoding='utf-8') as jsonfile:
        json.dump(files_metadata, jsonfile, ensure_ascii=False, indent=4)

    print(f"Index of files and their metadata has been saved to {json_output}")

# Call the functions
handle_two_factor()
index_to_json()

