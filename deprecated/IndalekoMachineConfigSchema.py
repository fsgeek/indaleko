'''
This module defines the database schema for the MachineConfig collection.

Project Indaleko
Copyright (C) 2024-2025 Tony Mason

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
import os
import sys

from icecream import ic


if os.environ.get('INDALEKO_ROOT') is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, 'Indaleko.py')):
        current_path = os.path.dirname(current_path)
    os.environ['INDALEKO_ROOT'] = current_path
    sys.path.append(current_path)

# pylint: disable=wrong-import-position
from IndalekoRecordSchema import IndalekoRecordSchema
from platforms.machine_config import IndalekoMachineConfigDataModel
# pylint: enable=wrong-import-position




class IndalekoMachineConfigSchema(IndalekoRecordSchema):
    '''Define the schema for use with the MachineConfig collection.'''

    def __init__(self):


        '''Initialize the schema for the MachineConfig collection.'''
        if not hasattr(self, 'data_mode'):
            self.data_model = IndalekoMachineConfigDataModel(
                **IndalekoMachineConfigDataModel.Config.json_schema_extra['example']
            )
        if not hasattr(self, 'base_type'):
            self.base_type = IndalekoMachineConfigDataModel
        machine_config_rules = self.data_model.model_dump_json()
        if not hasattr(self, 'rules'):
            self.rules = machine_config_rules
        else:
            self.rules.update(machine_config_rules)
        schema_id = 'https://activitycontext.work/schema/machineconfig.json'
        schema_title = 'Machine Configuration Schema'
        schema_description = 'Describes the machine where the data was indexed.'

    @staticmethod
    def get_old_schema():
        '''Return the old (static) schema for the MachineConfig.'''

        machine_config_schema = {
            '''
            This schema relates to the machine configuration collection,
            which captures meta-data about the machine where the data was indexed.
            '''
            "$schema": "https://json-schema.org/draft/2020-12/schema#",
            "$id": "https://activitycontext.work/schema/machineconfig.json",
            "title": "Data source schema",
            "description": "This schema describes information about the machine where the data was indesxed.",
            "type": "object",
            "rule" : {
                "Platform" : {
                    "type" : "object",
                    "properties" : {
                        "software" : {
                            "type" : "object",
                            "properties" : {
                                "OS" : {
                                    "type" : "string",
                                    "description" : "Name of the software.",
                                },
                                "Version" : {
                                    "type" : "string",
                                    "description" : "Version of the software.",
                                },
                            },
                            "required" : ["OS", "Version"],
                        },
                        "hardware" : {
                            "type" : "object",
                            "properties" : {
                                "CPU" : {
                                    "type" : "string",
                                    "description" : "Processor Architecture.",
                                },
                                "Version" : {
                                    "type" : "string",
                                    "description" : "Version of the hardware.",
                                },
                            },
                            "required" : ["CPU", "Version"],
                        },
                    },
                },
                "Captured" : {
                    "type" : "object",
                    "properties" : {
                        "Label" : {
                            "type" : "string",
                            "description" :
                            "UUID representing the semantic meaning of this timestamp.",
                            "format": "uuid",
                        },
                        "Value" : {
                            "type" : "string",
                            "description" : "Timestamp in ISO date and time format.",
                            "format" : "date-time",
                        },
                    },
                    "required" : ["Label", "Value"],
                },
                "required" : ["Captured"],
            }
        }
        assert 'Record' not in machine_config_schema['rule'], \
            'Record should not be in machine config schema.'
        machine_config_schema['rule']['Record'] = IndalekoRecordSchema().get_json_schema()['rule']
        machine_config_schema['rule']['required'].append('Record')
        return machine_config_schema

    def get_json_schema(self):
        '''Return the JSON schema for the MachineConfig collection.'''
        return IndalekoMachineConfigDataModel.get_json_schema()

    def get_arangodb_schema(self):
        '''Return the ArangoDB schema for the MachineConfig collection.'''
        return IndalekoMachineConfigDataModel.get_arangodb_schema()

def main():
    """Test the IndalekoMachineConfigSchema class."""
    machine_config_schema = IndalekoMachineConfigDataModel.get_json_schema()
    ic(machine_config_schema)
    ic(IndalekoMachineConfigSchema().get_json_schema())

if __name__ == "__main__":
    main()
