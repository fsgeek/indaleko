"""
This module defines the ActivityDataCharacteristics class.
This class is used to
describe the characteristics of activity data.  This is intended to be used to
help the system understand how to interact with the activity data.

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
import uuid

from pathlib import Path

from icecream import ic


if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

# pylint: disable=wrong-import-position
# pylint: enable=wrong-import-position


class ActivityDataCharacteristics:
    """Define the provider characteristics available for a data provider."""

    ACTIVITY_DATA_TEMPORAL = "521e13be-096e-4068-8f2a-4c162bd6a3fb"
    ACTIVITY_DATA_SPATIAL = "a77d0a02-a716-4d5e-a7e2-cabab87e00e6"
    ACTIVITY_DATA_COMMUNICATION = "c9f9f8d1-345f-4af6-ac65-23bdfec32e62"
    ACTIVITY_DATA_SEARCH = "c9f9f8d1-345f-4af6-ac65-23bdfec32e62"
    ACTIVITY_DATA_STORAGE = "ddfd3625-3c37-4b4c-b416-e0c4bd7ec010"
    ACTIVITY_DATA_COLLABORATION = "0b1014b0-b290-440c-98a7-5074f2bfa68e"
    ACTIVITY_DATA_APPLICATION_USAGE = "a6a87ac5-0263-4c97-807e-7c4965c6c7c1"
    ACTIVITY_DATA_SCHEDULED_EVENT = "267f3db7-5983-444c-a594-8ea9caf3ce7d"
    ACTIVITY_DATA_NETWORK = "75ad4c17-f8a9-451d-a197-a09c5e75fc06"
    ACTIVITY_DATA_SENSORY = "7ddd355d-706d-4856-94f3-ac44bfb2deca"
    ACTIVITY_DATA_MEDIA_CONSUMPTION = "3897c906-fb6d-4e6d-81c5-02334436e80d"
    ACTIVITY_DATA_SOCIAL_INTERACTION = "8c848e18-dd2b-4cc4-901f-7c32036eda4f"
    ACTIVITY_DATA_DEVICE_STATE = "8c7ac170-fe89-4d42-8ae1-de4c3c998917"
    ACTIVITY_DATA_ENVIRONMENTAL = "96b30aa4-635e-45e9-b3f2-1763c59a877a"
    ACTIVITY_DATA_SPOTIFY = "651b3b00-23f3-45ae-8d0e-79454a61ff3a"
    ACTIVITY_DATA_SYSTEM_ACTIVITY = "7e985763-ac4e-41b6-8b08-596d245be6c7"
    ACTIVITY_DATA_FILE_ACTIVITY = "008b6c9b-4428-4451-8bf4-36b4edfc123c"
    ACTIVITY_DATA_CLOUD_STORAGE = "ecf07280-0c05-4755-b674-bfe988fb7710"

    # available for use beyond this point
    uuid_to_label = {}  # noqa: RUF012

    _characteristic_prefix = "ACTIVITY_DATA_"

    def __init__(self) -> None:
        """Initialize the provider characteristics."""
        self.uuid_to_label = {}
        for label, value in ActivityDataCharacteristics.__dict__.items():
            if label.startswith(ActivityDataCharacteristics._characteristic_prefix):
                setattr(self, label + "_UUID", uuid.UUID(value))
                self.uuid_to_label[value] = label

    @staticmethod
    def get_activity_characteristics() -> dict:
        """Get the characteristics of the provider."""
        return {
            label: value
            for label, value in ActivityDataCharacteristics.__dict__.items()
            if label.startswith(ActivityDataCharacteristics._characteristic_prefix)
        }

    @staticmethod
    def get_activity_label(identifier: uuid.UUID) -> str | None:
        """Get the label for the provider."""
        return ActivityDataCharacteristics.uuid_to_label.get(identifier, None)

    @staticmethod
    def get_activity_uuid(label: str) -> uuid.UUID | None:
        """Get the UUID for the provider."""
        return getattr(ActivityDataCharacteristics, label + "_UUID", None)


def main() -> None:
    """Main entry point for the module."""
    ic("ActivityDataCharacteristics module test.")
    for (
        label,
        value,
    ) in ActivityDataCharacteristics.get_activity_characteristics().items():
        ic(label, value)
        ic(ActivityDataCharacteristics.get_activity_label(value))


if __name__ == "__main__":
    main()
