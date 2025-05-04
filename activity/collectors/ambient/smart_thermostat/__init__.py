"""
Init functionality for the ambient condition activity data providers.

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


# pylint: disable=wrong-import-position
from activity.collectors.ambient.smart_thermostat.ecobee_data_model import (
    EcobeeAmbientDataModel,
)

# pylint: enable=wrong-import-position

# Define what should be available when importing from this package
__all__ = [
    "EcobeeAmbientDataModel",
]
