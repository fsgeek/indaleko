'''
Indaleko Machine Configuration class.

Project Indaleko
Copyright (C) 2024 Tony Mason

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import argparse
import datetime
import json
import uuid
import socket
import platform
import os
import logging
import re

from IndalekoCollections import IndalekoCollections
from IndalekoDBConfig import IndalekoDBConfig
from IndalekoRecord import IndalekoRecord
from IndalekoMachineConfigSchema import IndalekoMachineConfigSchema
from Indaleko import Indaleko
from IndalekoServices import IndalekoService


class IndalekoMachineConfig(IndalekoRecord):
    """
    This is the generic class for machine config.  It should be used to create
    platform specific machine configuration classes.
    """

    indaleko_machine_config_uuid_str = "e65e412e-7862-4d81-affd-2bbd4f6b9a01"
    indaleko_machine_config_version_str = "1.0"
    indaleko_machine_config_captured_label_str = "eb7eaeed-6b21-4b6a-a586-dddca6a1d5a4"

    default_config_dir = "./config"

    Schema = IndalekoMachineConfigSchema.get_schema()

    def __init__(
        self: "IndalekoMachineConfig",
        timestamp: datetime = None,
        db: IndalekoDBConfig = None,
        **kwargs
    ):
        """
        Constructor for the IndalekoMachineConfig class. Takes a
        set of configuration data as a parameter and initializes the object.
        """
        self.machine_id = None
        if timestamp is None:
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        super().__init__(
            raw_data = b"",
            attributes = {},
            source = {
                "Identifier": IndalekoMachineConfig.indaleko_machine_config_uuid_str,
                "Version": IndalekoMachineConfig.indaleko_machine_config_version_str,
            },
        )
        self.platform = {}
        self.captured = {
            "Label": "Timestamp",
            "Value": timestamp,
        }
        collections = IndalekoCollections(db_config=db)
        self.collection = collections.get_collection(Indaleko.Indaleko_MachineConfig)
        assert self.collection is not None, "MachineConfig collection does not exist."
        service_name = "Indaleko Machine Config Service"
        if "service_name" in kwargs:
            service_name = kwargs["service_name"]
        service_identifier = self.indaleko_machine_config_uuid_str
        if "service_identifier" in kwargs:
            service_identifier = kwargs["service_identifier"]
        service_description = None
        if "service_description" in kwargs:
            service_description = kwargs["service_description"]
        service_version = self.indaleko_machine_config_version_str
        if "service_version" in kwargs:
            service_version = kwargs["service_version"]
        service_type = "Machine Configuration"
        if "service_type" in kwargs:
            service_type = kwargs["service_type"]
        self.machine_config_service = IndalekoService(service_name=service_name,
                              service_identifier=service_identifier,
                              service_description=service_description,
                              service_version=service_version,
                              service_type=service_type)
        assert self.machine_config_service is not None, "MachineConfig service does not exist."

    @staticmethod
    def find_config_files(directory : str, prefix : str) -> list:
        '''This looks for configuration files in the given directory.'''
        if not isinstance(prefix, str):
            raise AssertionError(f'prefix must be a string, not {type(prefix)}')
        if not isinstance(directory, str):
            raise AssertionError(f'directory must be a string, not {type(directory)}')
        return [x for x in os.listdir(directory)
                if x.startswith(prefix)
                and x.endswith('.json')]

    @staticmethod
    def get_guid_timestamp_from_file_name(file_name : str, prefix : str, suffix : str = 'json') -> tuple:
        '''
        Get the machine configuration captured by powershell.
        Note that this PS script requires admin privileges so it might
        be easier to do this in an application that elevates on Windows so it
        can be done dynamically.  For now, we assume it has been captured.
        '''
        if not isinstance(file_name, str):
            raise AssertionError(f'file_name must be a string, not {type(file_name)}')
        if not isinstance(prefix, str):
            raise AssertionError(f'prefix must be a string, not {type(prefix)}')
        if suffix[0] == '.':
            suffix = suffix[1:]
        # Regular expression to match the GUID and timestamp
        pattern = f"(?:.*[/])?{prefix}-(?P<guid>[a-fA-F0-9\\-]+)-(?P<timestamp>\\d{4}-\\d{2}-\\d{2}T\\d{2}-\\d{2}-\\d{2}\\.\\d+Z)\\.{suffix}"
        match = re.match(pattern, file_name)
        assert match, f'Filename format not recognized for {file_name} with re {pattern}.'
        guid = uuid.UUID(match.group("guid"))
        timestamp = match.group("timestamp").replace("-", ":")
        assert timestamp[-1] == 'Z', 'Timestamp must end with Z'
        # %f can only handle up to 6 digits and it seems Windows gives back
        # more sometimes. Note this truncates, it doesn't round.  I doubt
        # it matters.
        timestamp_parts = timestamp.split('.')
        fractional_part = timestamp_parts[1][:6] # truncate to 6 digits
        ymd, hms = timestamp_parts[0].split('T')
        timestamp = ymd.replace(':', '-') + 'T' + hms + '.' + fractional_part + '+00:00'
        timestamp = datetime.datetime.fromisoformat(timestamp)
        return (file_name, guid, timestamp)


    @staticmethod
    def get_most_recent_config_file(config_dir : str, prefix : str, suffix : str = '.json') -> str:
        '''Get the most recent machine configuration file.'''
        candidates = [x for x in os.listdir(config_dir) if
                    x.startswith(prefix) and x.endswith(suffix)]
        assert len(candidates) > 0, f'At least one {prefix} file should exist'
        candidate_files = [(timestamp, filename)
                        for filename, guid, timestamp in
                        [IndalekoMachineConfig.get_guid_timestamp_from_file_name(x, prefix, suffix)
                            for x in candidates]]
        candidate_files.sort(key=lambda x: x[0])
        candidate = candidate_files[0][1]
        if config_dir is not None:
            candidate = os.path.join(config_dir, candidate)
        return candidate


    def set_platform(self, platform_data: dict) -> None:
        """
        This method sets the platform information for the machine.
        """
        assert isinstance(
            platform_data, dict
        ), f"platform must be a dict (not {type(platform_data)})"
        assert "software" in platform_data, "platform must contain a software field"
        assert isinstance(
            platform_data["software"], dict
        ), f'platform["software"] must be a dictionary, not {type(platform_data["software"])}'
        assert isinstance(
            platform_data["software"]["OS"], str
        ), f'platform must contain a string OS field, not {type(platform_data["software"]["OS"])}'
        assert isinstance(
            platform_data["software"]["Version"], str
        ), "platform must contain a string version field"
        assert isinstance(
            platform_data["software"]["Architecture"], str
        ), "platform must contain a string architecture field"
        assert "hardware" in platform_data, "platform must contain a hardware field"
        assert isinstance(
            platform_data["hardware"], dict
        ), 'platform["hardware"] must be a dictionary'
        assert isinstance(
            platform_data["hardware"]["CPU"], str
        ), "platform must contain a string CPU field"
        assert isinstance(
            platform_data["hardware"]["Version"], str
        ), "platform must contain a string version field"
        assert isinstance(
            platform_data["hardware"]["Cores"], int
        ), "platform must contain an integer cores field"
        self.platform = platform_data
        return self

    def get_platform(self) -> dict:
        """
        This method returns the platform information for the machine.
        """
        if hasattr(self, "Platform"):
            return self.platform
        return None

    def set_captured(self, timestamp: datetime) -> None:
        """
        This method sets the timestamp for the machine configuration.
        """
        if isinstance(timestamp, dict):
            assert "Label" in timestamp, "timestamp must contain a Label field"
            assert (
                timestamp["Label"] == "Timestamp"
            ), "timestamp must have a Label of Timestamp"
            assert "Value" in timestamp, "timestamp must contain a Value field"
            assert isinstance(
                timestamp["Value"], str
            ), "timestamp must contain a string Value field"
            assert self.validate_iso_timestamp(
                timestamp["Value"]
            ), f'timestamp {timestamp["Value"]} is not a valid ISO timestamp'
            self.captured = {
                "Label": "Timestamp",
                "Value": timestamp["Value"],
            }
        elif isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.isoformat()
        else:
            assert isinstance(
                timestamp, str
            ), f"timestamp must be a string or timestamp (not {type(timestamp)})"
        self.captured = {
            "Label": IndalekoMachineConfig.indaleko_machine_config_captured_label_str,
            "Value": timestamp,
            "Description" : "Timestamp when this machine configuration was captured.",
        }
        return self

    def get_captured(self) -> datetime.datetime:
        """
        This method returns the timestamp for the machine configuration.
        """
        if hasattr(self, "captured"):
            return self.captured
        return None

    def parse_config_file(self) -> None:
        """
        This method parses the configuration data from the config file.
        """
        raise AssertionError("This method should be overridden by the derived classes.")

    def set_machine_id(self, machine_id) -> None:
        """
        This method sets the machine ID for the machine configuration.
        """
        if isinstance(machine_id, str):
            assert self.validate_uuid_string(
                machine_id
            ), f"machine_id {machine_id} is not a valid UUID."
        elif isinstance(machine_id, uuid.UUID):
            machine_id = str(machine_id)
        self.machine_id = machine_id
        return self

    def get_machine_id(self) -> str:
        """
        This method returns the machine ID for the machine configuration.
        """
        if hasattr(self, "machine_id"):
            return self.machine_id
        return None

    def write_config_to_db(self) -> None:
        """
        This method writes the configuration to the database.
        """
        assert hasattr(
            self, "machine_id"
        ), "machine_id must be set before writing to the database."
        assert self.validate_uuid_string(
            self.machine_id
        ), f"machine_id {self.machine_id} is not a valid UUID."
        if not IndalekoMachineConfigSchema.is_valid_record(self.to_dict()):
            print("Invalid record:")
            print(json.dumps(self.to_dict(), indent=4))
            raise AssertionError("Invalid record.")
        self.collection.insert(self.to_json(), overwrite=True)

    @staticmethod
    def load_config_from_file() -> dict:
        """
        This method creates a new IndalekoMachineConfig object from an
        existing config file.  This must be overridden by the platform specific
        machine configuration implementation.
        """
        raise AssertionError("This method should be overridden by the derived classes.")

    @staticmethod
    def find_configs_in_db(source_id : str) -> list:
        """
        This method finds all the machine configs with given source_id.
        """
        if not IndalekoMachineConfig.validate_uuid_string(source_id):
            raise AssertionError(f"source_id {source_id} is not a valid UUID.")
        collections = IndalekoCollections()
        # Using spaces in names complicates things, but this does work.
        cursor = collections.db_config.db.aql.execute(
            f'FOR doc IN {Indaleko.Indaleko_MachineConfig} FILTER '+\
             'doc.Record["Source Identifier"].Identifier == ' +\
             '@source_id RETURN doc',
            bind_vars={'source_id': source_id})
        entries = [entry for entry in cursor]
        return entries

    @staticmethod
    def delete_config_in_db(machine_id: str) -> None:
        """
        This method deletes the specified machine config from the database.
        """
        assert IndalekoMachineConfig.validate_uuid_string(
            machine_id
        ), f"machine_id {machine_id} is not a valid UUID."
        IndalekoCollections().get_collection(Indaleko.Indaleko_MachineConfig).delete(machine_id)

    @staticmethod
    def load_config_from_db(machine_id: str) -> "IndalekoMachineConfig":
        """
        This method loads the configuration from the database.
        """
        assert IndalekoMachineConfig.validate_uuid_string(
            machine_id
        ), f"machine_id {machine_id} is not a valid UUID."
        entries = IndalekoCollections().get_collection(Indaleko.Indaleko_MachineConfig).find_entries(_key=machine_id)
        if len(entries) == 0:
            return None  # not found
        assert (
            len(entries) == 1
        ), f"Found {len(entries)} entries for machine_id {machine_id} - multiple entries case not handled."
        entry = entries[0]
        machine_config = IndalekoMachineConfig()
        machine_config.set_platform(entry["Platform"])
        # temporary: I've changed the shape of the database, so I'll need to
        # work around it temporarily
        if 'Source' in entry and \
            isinstance(entry["Source"], str) and \
            "Version" in entry:
            machine_config.set_source(
                {
                    "Identifier": entry["Source"],
                    "Version": entry["Version"],
                }
            )
        else:
            assert isinstance(
                entry["Source"], dict
            ), f'entry[Source"] must be a dict, not {type(entry["Source"])}'
            machine_config.set_source(entry["Source"])
        machine_config.set_captured(entry["Captured"])
        machine_config.set_base64_data(entry["Data"])
        machine_config.set_attributes(entry["Attributes"])
        machine_config.set_machine_id(machine_id)
        return machine_config

    @staticmethod
    def get_machine_name() -> str:
        """This retrieves a user friendly machine name."""
        return socket.gethostname()

    def to_dict(self) -> dict:
        """
        This method returns the dictionary representation of the machine config.
        """
        record = {}
        record['Record'] = super().to_dict()
        record["Platform"] = self.platform
        assert self.captured is not None, "Captured timestamp must be set."
        record["Captured"] = self.captured
        if hasattr(self, "machine_id"):
            record["_key"] = self.machine_id
        record["hostname"] = IndalekoMachineConfig.get_machine_name()
        return record

    def to_json(self, indent: int = 4) -> str:
        """
        This method returns the JSON representation of the machine config.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @staticmethod
    def build_config(**kwargs) -> "IndalekoMachineConfig":
        """This method builds a machine config from the specified parameters."""
        assert "os" in kwargs, "OS must be specified"
        assert isinstance(kwargs["os"], str), "OS must be a string"
        assert "arch" in kwargs, "Architecture must be specified"
        assert isinstance(kwargs["arch"], str), "Architecture must be a string"
        assert "os_version" in kwargs, "OS version must be specified"
        assert isinstance(kwargs["os_version"], str), "OS version must be a string"
        assert "cpu" in kwargs, "CPU must be specified"
        assert isinstance(kwargs["cpu"], str), "CPU must be a string"
        assert "cpu_version" in kwargs, "CPU version must be specified"
        assert isinstance(kwargs["cpu_version"], str), "CPU version must be a string"
        assert "cpu_cores" in kwargs, "CPU cores must be specified"
        assert isinstance(kwargs["cpu_cores"], int), "CPU cores must be an integer"
        assert "source_id" in kwargs, "source must be specified"
        assert isinstance(kwargs["source_id"], str), "source must be a dict"
        assert "source_version" in kwargs, "source version must be specified"
        assert isinstance(
            kwargs["source_version"], str
        ), "source version must be a string"
        assert "attributes" in kwargs, "Attributes must be specified"
        assert "data" in kwargs, "Data must be specified"
        assert "machine_id" in kwargs, "Machine ID must be specified"
        if "timestamp" in kwargs:
            assert IndalekoMachineConfig.validate_iso_timestamp(
                kwargs["timestamp"]
            ), f'Timestamp {kwargs["timestamp"]} is not a valid ISO timestamp'
            timestamp = kwargs["timestamp"]
        else:
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if "machine_config" not in kwargs:
            machine_config = IndalekoMachineConfig()
        else:
            machine_config = kwargs["machine_config"]
        machine_config.set_platform(
            {
                "software": {
                    "OS": kwargs["os"],
                    "Architecture": kwargs["arch"],
                    "Version": kwargs["os_version"],
                },
                "hardware": {
                    "CPU": kwargs["cpu"],
                    "Version": kwargs["cpu_version"],
                    "Cores": kwargs["cpu_cores"],
                },
            }
        )
        machine_config.set_captured(timestamp)
        machine_config.set_source(
            {
                "Identifier": kwargs["source_id"],
                "Version": kwargs["source_version"],
            }
        )
        machine_config.set_attributes(kwargs["attributes"])
        machine_config.set_base64_data(kwargs["data"])
        machine_config.set_machine_id(kwargs["machine_id"])
        return machine_config

def get_script_name(platform_name : str = platform.system()) -> str:
    '''This routine returns the name of the script.'''
    script_name = f'Indaleko{platform_name}MachineConfig.py'
    return script_name


def check_linux_prerequisites() -> None:
    '''This routine checks that the Linux system prerequisites are met.'''
    # Linux has no pre-requisites at the current time.
    return True

def check_macos_prerequisites() -> None:
    '''This routine checks that the MacOS system prerequisites are met.'''
    # TBD
    return False

def check_windows_prerequisites(config_dir : str = Indaleko.default_config_dir) -> None:
    '''This routine checks that the Windows system prerequisites are met.'''
    # This is tough to do cleanly, since the default name is defined in
    # IndalekoWindowsMachineConfig.py and that includes this file.
    candidates = [x for x in os.listdir(config_dir) if x.startswith('windows')]
    if len(candidates) == 0:
        print(f'No Windows machine config files found in {config_dir}')
        print('To create a Windows machine config, run: '+ \
              'windows-hardware-info.ps1 from an elevated PowerShell prompt.')
        print('Note: this will require enable execution of PowerShell scripts.')
    return False

def add_command(args: argparse.Namespace) -> None:
    '''This routine adds a machine config to the database.'''
    logging.info('Adding machine config for %s', args.platform)
    if args.platform == 'Linux':
        check_linux_prerequisites()
        logging.info('Linux prerequisites met')
        cmd_string = f'python3 {get_script_name(args.platform)}'
        cmd_string += f' --configdir {args.configdir}'
        cmd_string += f' --timestamp {args.timestamp}'
        logging.info('Recommending: <%s> for Linux machine config', cmd_string)
        print(f'Please run:\n\t{cmd_string}')
    elif args.platform == 'Darwin':
        check_macos_prerequisites()
    elif args.platform == 'Windows':
        check_windows_prerequisites()
    return

def list_command(args: argparse.Namespace) -> None:
    '''This routine lists the machine configs in the database.'''
    print(args)
    return

def delete_command(args: argparse.Namespace) -> None:
    '''This routine deletes a machine config from the database.'''
    print(args)
    return

def main():
    '''
    This is the main function for the IndalekoMachineConfig class.
    '''
    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    file_name = Indaleko.generate_file_name(
        suffix='log',
        platform=platform.system(),
        service='machine_config',
        timestamp=timestamp)
    default_log_file = os.path.join(Indaleko.default_log_dir, file_name)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    parser_add = subparsers.add_parser('add', help='Add a machine config')
    parser_add.add_argument('--platform',
                            type=str,
                            default=platform.system(),
                            help='Platform to use')
    parser_list = subparsers.add_parser('list', help='List machine configs')
    parser_list.add_argument('--files',
                             default=False,
                             action='store_true',
                             help='Source ID')
    parser_list.add_argument('--db',
                             type=str,
                             default=True,
                             help='Source ID')
    parser_delete = subparsers.add_parser('delete', help='Delete a machine config')
    parser_delete.add_argument('--platform',
                               type=str,
                               default=platform.system(),
                               help='Platform to use')
    parser.add_argument(
        '--log',
        type=str,
        default=default_log_file,
        help='Log file name to use')
    parser.add_argument('--configdir',
                        type=str,
                        default=IndalekoMachineConfig.default_config_dir,
                        help='Configuration directory to use')
    parser.add_argument('--timestamp', type=str,
                       default=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       help='Timestamp to use')
    args = parser.parse_args()
    if args.log is not None:
        logging.basicConfig(filename=args.log, level=logging.DEBUG)
        logging.info('Starting Indaleko Machine Config')
        logging.info('Logging to %s', args.log)  # Fix: Use lazy % formatting
    if args.command == 'add':
        add_command(args)
    elif args.command == 'list':
        list_command(args)
    elif args.command == 'delete':
        delete_command(args)
    else:
        raise AssertionError(f'Unknown command {args.command}')
    logging.info('Done with Indaleko Machine Config')

if __name__ == "__main__":
    main()
