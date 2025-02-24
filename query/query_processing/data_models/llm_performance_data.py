
"""
This module defines the query history data model for Indaleko.

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
"""
import json
import os
import sys
from textwrap import dedent

from datetime import datetime, timezone
from typing import Any, TypeVar, Union

from pydantic import Field, field_validator, BaseModel

if os.environ.get('INDALEKO_ROOT') is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, 'Indaleko.py')):
        current_path = os.path.dirname(current_path)
    os.environ['INDALEKO_ROOT'] = current_path
    sys.path.append(current_path)

T = TypeVar('T', bound='LLMPerformanceData')

# pylint: disable=wrong-import-position
# pylint: enable=wrong-import-position


class LLMPerformanceData(BaseModel):
    '''This class is used to capture performance data for an LLM.'''
    LLMName: str = Field(
        ...,
        title='LLMName',
        description='The name of the LLM.'
    )

    LLMOperation: dict = Field(
        ...,
        title='LLMOperation',
        description='The operation that was submitted to the LLM.'
    )

    RawResults: Union[list[dict[str, Any]]] = Field(
        None,
        title='Results',
        description='The raw results of the LLM operation.'
    )

    AnalyzedResults: Union[list[dict[str, Any]], None] = Field(
        ...,
        title='AnalyzedResults',
        description='The analyzed results of the LLM operation.'
    )

    StartTime: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        title='StartTime',
        description='The timestamp of when the LLM operation started.'
    )

    IntermediateTimes: Union[dict[str, datetime], None] = Field(
        None,
        title='IntermediateTimes',
        description=dedent(
            """
            Labels and timestamps for intermediate steps in the LLM operation.
            (Optional)
            """
        )
    )

    EndTime: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        title='EndTime',
        description='The timestamp of when the LLM operation ended.'
    )

    ResourceUtilization: Union[dict[str, dict[str, Any]], None] = Field(
        None,
        title='ResourceUtilization',
        description='Resource utilization metrics such as CPU and memory usage.'
    )

    @staticmethod
    def validate_timestamp(ts: Union[str, datetime]) -> datetime:
        '''Ensure that the timestamp is in UTC'''
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts

    @field_validator('StartTime', mode='before')
    @classmethod
    def ensure_starttime(cls, value: datetime):
        return cls.validate_timestamp(value)

    @field_validator('EndTime', mode='before')
    @classmethod
    def ensure_endtime(cls, value: datetime):
        return cls.validate_timestamp(value)

    @field_validator('IntermediateTimes', mode='before')
    @classmethod
    def ensure_intermediate_times(cls, value: dict[str, datetime]):
        for label, timestamp in value.items():
            cls.validate_timestamp(timestamp)
        return value

    class Config:
        '''Sample configuration data for the data model.'''
        json_schema_extra = {
                    "example": {
                        "LLMName": "GPT-3",
                        "LLMOperation": {
                            "Operation": "Query",
                            "Query": "What is the capital of France?"
                        },
                        "RawResults": [
                            {
                                "Answer": "Paris",
                                "Confidence": 0.95
                            }
                        ],
                        "AnalyzedResults": [
                            {
                                "Answer": "Paris",
                                "Confidence": 0.95,
                                "Intent": "Respond",
                                "Rationale": "The user asked for the capital of France."
                            }
                        ],
                        "StartTime": "2022-01-01T00:00:00Z",
                        "IntermediateTimes": {
                            "Preprocessing": "2022-01-01T00:00:01Z",
                            "Inference": "2022-01-01T00:00:02Z",
                            "Postprocessing": "2022-01-01T00:00:03Z",
                        },
                        "EndTime": "2022-01-01T00:00:04Z",
                        "ResourceUtilization": {
                            "Preprocessing": {
                                "CPU": 0.95,
                                "Memory": 0.75
                            },
                            "Inference": {
                                "CPU": 0.95,
                                "Memory": 0.75
                            },
                            "Postprocessing": {
                                "CPU": 0.95,
                                "Memory": 0.75
                            }
                        }
                    },
                }


def main():
    '''This allows testing the data model.'''
    print(
        json.dumps(
            json.loads(LLMPerformanceData(**LLMPerformanceData.Config.json_schema_extra['example']).model_dump_json()),
            indent=2
        )
    )


if __name__ == '__main__':
    main()
