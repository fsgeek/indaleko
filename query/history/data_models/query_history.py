
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

import os
import sys

from typing import Any, Union
from textwrap import dedent

from pydantic import Field, BaseModel

if os.environ.get('INDALEKO_ROOT') is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, 'Indaleko.py')):
        current_path = os.path.dirname(current_path)
    os.environ['INDALEKO_ROOT'] = current_path
    sys.path.append(current_path)


# pylint: disable=wrong-import-position
from data_models.base import IndalekoBaseModel  # noqa: E402
from data_models.record import IndalekoRecordDataModel  # noqa: E402
from query.query_processing.data_models.parser_data import ParserResults  # noqa: E402
from query.query_processing.data_models.llm_performance_data import LLMPerformanceData  # noqa: E402
from query.query_processing.data_models.query_input import StructuredQuery  # noqa: E402
from query.query_processing.data_models.translator_response import TranslatorOutput  # noqa: E402
# pylint: enable=wrong-import-position


class QueryHistoryData(BaseModel):
    '''This class defines the baseline data that is stored in the query history.'''
    OriginalQuery: str = Field(
        ...,
        title='OriginalQuery',
        description='The original query from the user.'
    )

    ParsedResults: ParserResults = Field(
        ...,
        title='ParsingResults',
        description='The results of parsing the query.'
    )

    LLMQuery: StructuredQuery = Field(
        ...,
        title='LLMQuery',
        description='The structured query submitted to the LLM for processing.'
    )

    TranslatedOutput: TranslatorOutput = Field(
        ...,
        title='TranslatedOutput',
        description='The translated output from the LLM.'
    )

    Facets: Union[list[dict[str, Any]], None] = Field(
        ...,
        title='Facets',
        description='The facets extracted from the query results.'
    )

    RankedResults: Union[list[dict[str, Any]], None] = Field(
        ...,
        title='RankedResults',
        description='The ranked results of the database query.'
    )

    PerformanceData: Union[LLMPerformanceData, None] = Field(
        None,
        title='PerformanceData',
        description='The performance data for the query.'
    )

    class Config:
        '''Sample configuration data for the data model.'''
        json_schema_extra = {
            "example": {
                "OriginalQuery": "Find all the people who live in New York City.",
                "ParsedResults": ParserResults.Config.json_schema_extra['example'],
                "LLMQuery": StructuredQuery.Config.json_schema_extra['example'],
                "TranslatedOutput": TranslatorOutput.Config.json_schema_extra['example'],
                "Facets": [],
                "RankedResults": [],
                "PerformanceData": LLMPerformanceData.Config.json_schema_extra['example']
            }
        }


class IndalekoQueryHistoryDataModel(IndalekoBaseModel):
    '''
    This class defines the data model for the Indaleko query history.
    '''
    Record: IndalekoRecordDataModel = Field(
        ...,
        title='Record',
        description='The record associated with the performance data.'
    )

    QueryHistory: Union[QueryHistoryData, None] = Field(
        None,
        title='QueryHistory',
        description=dedent(
            """
            The query history data. If omitted, the query history
            can be retrieved from the database using the record,
            as the Data element in the Record conforms to this
            schema (or a successor schema - use the version number.)
            """
        )
    )

    class Config:
        '''Sample configuration data for the data model.'''
        json_schema_extra = {
            "example": {
                "Record": IndalekoRecordDataModel.Config.json_schema_extra['example'],
                "QueryHistory": QueryHistoryData.Config.json_schema_extra['example'],
            }
        }


def main():
    '''This allows testing the data model.'''
    IndalekoQueryHistoryDataModel.test_model_main()


if __name__ == '__main__':
    main()
