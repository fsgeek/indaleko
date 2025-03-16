"""
This is the abstract base class that activity data providers use.

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

import datetime
import os
import sys
import uuid

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from icecream import ic

if os.environ.get("INDALEKO_ROOT") is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, "Indaleko.py")):
        current_path = os.path.dirname(current_path)
    os.environ["INDALEKO_ROOT"] = current_path
    sys.path.append(current_path)

# pylint: disable=wrong-import-position
from activity.characteristics import ActivityDataCharacteristics

# pylint: enable=wrong-import-position


class CollectorBase(ABC):
    """
    Abstract base class for activity data providers.

    Note: this class is fairly minimal, and I expect that it will grow as we
    develop the system further.
    """

    @abstractmethod
    def get_collector_characteristics(self) -> List[ActivityDataCharacteristics]:
        """
        This call returns the characteristics of the data provider.  This is
        intended to be used to help users understand the data provider and to
        help the system understand how to interact with the data provider.

        Returns:
            Dict: A dictionary containing the characteristics of the provider.
        """

    @abstractmethod
    def get_collector_name(self) -> str:
        """Get the name of the provider"""

    @abstractmethod
    def get_provider_id(self) -> uuid.UUID:
        """Get the UUID for the provider"""

    @abstractmethod
    def retrieve_data(self, data_id: uuid.UUID) -> Dict:
        """
        This call retrieves the data associated with the provided data_id.

        Args:
            data_id (uuid.UUID): The UUID that represents the data to be
            retrieved.

        Returns:
            Dict: The data associated with the data_id.
        """

    @abstractmethod
    def get_cursor(self, activity_context: uuid.UUID) -> uuid.UUID:
        """Retrieve the current cursor for this data provider
        Input:
             activity_context: the activity context into which this cursor is
             being used
         Output:
             The cursor for this data provider, which can be used to retrieve
             data from this provider (via the retrieve_data call).
        """

    @abstractmethod
    def cache_duration(self) -> datetime.timedelta:
        """
        Retrieve the maximum duration that data from this provider may be
        cached
        """

    @abstractmethod
    def get_description(self) -> str:
        """
        Retrieve a description of the data provider. Note: this is used for
        prompt construction, so please be concise and specific in your
        description.
        """

    @abstractmethod
    def get_json_schema(self) -> dict:
        """
        Retrieve the JSON data schema to use for the database.
        """

    @abstractmethod
    def collect_data(self) -> None:
        """Collect data from the provider"""

    @abstractmethod
    def process_data(self, data: Any) -> Dict[str, Any]:
        """Process the collected data"""

    @abstractmethod
    def store_data(self, data: Dict[str, Any]) -> None:
        """Store the processed data"""


def main():
    """This is a test interface for the provider base."""
    ic("ProviderBase test interface")


if __name__ == "__main__":
    main()
