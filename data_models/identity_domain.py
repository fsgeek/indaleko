'''
This module defines the data model for the identity domain information.

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
import os
import sys
import uuid

from typing import List, Union

from pydantic import Field, BaseModel
from icecream import ic

if os.environ.get('INDALEKO_ROOT') is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, 'Indaleko.py')):
        current_path = os.path.dirname(current_path)
    os.environ['INDALEKO_ROOT'] = current_path
    sys.path.append(current_path)

# pylint: disable=wrong-import-position
from data_models.base import IndalekoBaseModel
from data_models.record import IndalekoRecordDataModel
from data_models.timestamp import IndalekoTimestampDataModel
from data_models.semantic_attribute import IndalekoSemanticAttributeDataModel
from data_models.i_uuid import IndalekoUUIDDataModel
# pylint: enable=wrong-import-position

class IndalekoIdentityDomainDataModel(IndalekoBaseModel):
    '''This class captures identity domain information.'''

    Record : IndalekoRecordDataModel = Field(None,
                                    title='Record',
                                    description='The record associated with the identity domain declaration.')

    Domain : IndalekoUUIDDataModel = Field(None,
                        title='Domain',
                        description='The identifier assigned to this identity domain.')

    Description : str = Field(None,
                        title='Description',
                        description='Description of the identity domain.')

    class Config:
        '''
        This class defines the configuration for the data model.
        '''
        json_schema_extra = {
            "example" : {
                "Record" : IndalekoRecordDataModel.Config.json_schema_extra['example'],
                "Domain" : IndalekoUUIDDataModel.Config.json_schema_extra['example'],
                "Description" : "This is a sample description of the identity domain."
            }
        }

def main():
    '''This allows testing the data model'''
    ic('Testing the IdentityDomain data model')
    IndalekoIdentityDomainDataModel.test_model_main()

if __name__ == '__main__':
    main()