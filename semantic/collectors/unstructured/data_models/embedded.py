"""
This module defines the data model for the checksum data collector.

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

# standard imports
import json
import mimetypes
import os
import sys
from datetime import UTC, datetime

# third-party imports
from uuid import UUID, uuid4

from pydantic import AwareDatetime, Field, field_validator


from data_models.base import IndalekoBaseModel

# Indaleko imports
# pylint: disable=wrong-import-position
from Indaleko import Indaleko

# pylint: enable=wrong-import-position


class UnstructuredEmbeddedDataModel(IndalekoBaseModel):
    """
    This class defines the data model for the unstructured data collector.
    """

    ElementId: UUID = Field(
        default_factory=uuid4,
        description="The unique identifier for the unstructured data element.",
    )
    FileUUID: UUID = Field(
        ...,
        desdription="The UUID for the file object in the database.",
    )
    FileType: str | None = Field(..., description="The MIME type of the file.")
    LastModified: AwareDatetime = Field(
        ...,
        description="The last modified time for the file.",
    )
    PageNumber: int | None = Field(
        None,
        title="Page Number",
        description="The page number where the element starts.",
    )
    Languages: list[str] = Field(
        ...,
        description="The languages detected in the element.",
    )
    EmphasizedTextContents: list[str] | None = Field(
        None,
        title="Emphasized Text Contents",
        description="The emphasized text contents.",
    )
    EmphasizedTextTags: list[str] | None = Field(
        None,
        title="Emphasized Text Tags",
        description="Tags corresponding (e.g,. bold, italic) for emphasized text.",
    )
    Text: str = Field(..., description="The text content of the element.")
    Type: str = Field(
        None,
        description="The type of the extracted element, such as 'Title' or 'UncagegorizedText'.",
    )
    Raw: str = Field(..., description="The raw data from Unstructured.")

    @classmethod
    @field_validator("FileType")
    def validate_file_type(cls, v):
        if v is None:
            return v
        if not mimetypes.guess_extension(v):
            raise ValueError(f"Invalid MIME type: {v}")
        return v

    @classmethod
    @field_validator("LastModified")
    def validate_last_modified(cls, value: datetime):
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value

    class Config:
        """Sample configuration data for the data model."""

        json_schema_extra = {
            "example": {
                "ElementId": "1b869a4a4f802edd162e53421854f48f",
                "FileUUID": "6c82fb8c-b5c5-4fa3-8017-bded9ba39532",
                "FileType": "applicatapplication/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "LastModified": "2023-09-27T19:41:36Z",
                "PageNumber": 2,
                "Languages": ["ind", "ron"],
                "Text": "Singapore, Asia",
                "Type": "Title",
                "Raw": Indaleko.encode_binary_data(
                    json.dumps(
                        {
                            "element_id": "1b869a4a4f802edd162e53421854f48f",
                            "metadata": {
                                "file_directory": "/app/downloads",
                                "filename": "Football data_source.xlsx",
                                "filetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                "languages": ["ind", "ron"],
                                "last_modified": "2023-09-27T19:41:36",
                                "page_name": "Countries",
                                "page_number": 2,
                            },
                            "text": "Singapore, Asia",
                            "type": "Title",
                        },
                    ),
                ),
            },
        }


def main():
    """This allows testing the data model."""
    UnstructuredEmbeddedDataModel.test_model_main()


if __name__ == "__main__":
    main()
