"""
This module defines the database schema for any database record conforming to
the Indaleko Record requirements.

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
"""

import os
import sys
import uuid

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, UTC
from icecream import ic

if os.environ.get('INDALEKO_ROOT') is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, 'Indaleko.py')):
        current_path = os.path.dirname(current_path)
    os.environ['INDALEKO_ROOT'] = current_path
    sys.path.append(current_path)

class IndalekoTimestampDataModel(BaseModel):
    '''
    This class defines the UUID data model for Indaleko.
    '''
    Label : uuid.UUID = Field(...,
                              title='Label',
                              description='UUID representing the semantic meaning of this timestamp.',
                              example='12345678-1234-5678-1234-567812345678')
    Value : datetime = Field(...,
                             title='Value',
                             description='The timestamp value.',
                             example='2024-01-01T00:00:00Z')

    Description : Optional[str] = Field(None,
                                  title='Description',
                                  description='A human-readable label for the UUID.',
                                  example='This is a sample timestamp.')

    class Config:
        json_schema_extra = {
            "example": {
                "Label": "12345678-1234-5678-1234-567812345678",
                "Value": "2024-01-01T00:00:00Z",
                "Description": "This is a sample IndalekoUUID."
            }
        }

    def serialize(self) -> Dict[str, Any]:
        '''Serialize the data model'''
        return self.model_dump(exclude_unset=True)

    @staticmethod
    def deserialize(data : Dict[str, Any]) -> 'IndalekoUUID':
        '''Deserialize the data model'''
        obj = IndalekoTimestampDataModel(**data)
        if obj.Value.tzinfo is None:
            # guarantee that the timestamp has a timezone
            # so that when we serialize it, ArangoDB won't choke on it.
            obj.Value = obj.Value.replace(tzinfo=UTC)
        return obj

def main():
    '''This allows testing the data model'''
    data = IndalekoTimestampDataModel(
        Label=uuid.uuid4(),
        Value=datetime.now(UTC),
        Description='This is a sample IndalekoUUID.')
    ic(data)
    ic(data.json())
    ic(data.dict())
    serial_data = data.serialize()
    ic(type(serial_data))
    ic(serial_data)
    data_check = IndalekoTimestampDataModel.deserialize(serial_data)
    assert data_check == data
    ic(IndalekoTimestampDataModel.schema_json())

if __name__ == '__main__':
    main()