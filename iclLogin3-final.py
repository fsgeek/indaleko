# iclLogin1.py
import sys
from creds import iclAPI  # Importing the iclAPI object from creds.py

# Check if two-factor authentication (2FA) is required
if iclAPI.requires_2fa:
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

# If the account has two-step authentication (2SA) enabled
elif iclAPI.requires_2sa:
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

# Now you can proceed to interact with your iCloud account as authenticated

# iclLogin2.py
# ... (the rest of your login code) ...

# Logged in successfully
print("Logged in successfully.")

# Now let's try to list the Account devices
print("Listing devices associated with the account...")

# devices = iclAPI.devices
# for device_id, device in devices.items():
#     print(f"Device ID: {device_id}")
#     print(f"  Device Name: {device.data['name']}")
#     print(f"  Device Model: {device.data['modelDisplayName']}")
#     print(f"  Device Status: {device.data['deviceStatus']}")
#     print(f"  Battery Level: {device.data.get('batteryLevel', 'Unknown')}")
