"""
This module defines an ecobee-specific implementation of the thermostat
ambient data collection model.

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
from typing import Optional
from pydantic import Field, field_validator

if os.environ.get('INDALEKO_ROOT') is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, 'Indaleko.py')):
        current_path = os.path.dirname(current_path)
    os.environ['INDALEKO_ROOT'] = current_path
    sys.path.append(current_path)

# pylint: disable=wrong-import-position
from activity.collectors.ambient.data_models.smart_thermostat import ThermostatSensorData
# pylint: enable=wrong-import-position

class EcobeeAmbientData(ThermostatSensorData):
    """
    Ecobee-specific implementation of the thermostat sensor ambient data model.
    Extends ThermostatSensorData to maintain the common structure while adding
    ecobee-specific attributes and capabilities.
    """
    # Ecobee identification - useful for tracking specific devices
    device_id: str = Field(
        ...,
        description="Ecobee device identifier",
        pattern="^[a-zA-Z0-9]+$"
    )

    device_name: str = Field(
        ...,
        description="Name assigned to the thermostat",
        min_length=1
    )

    # Additional ecobee-specific sensor data
    aux_heat_active: Optional[bool] = Field(
        None,
        description="Whether auxiliary/emergency heat is active"
    )

    dehumidifier_mode: Optional[str] = Field(
        None,
        description="Current dehumidifier setting",
        pattern="^(auto|on|off)$"
    )

    ventilator_mode: Optional[str] = Field(
        None,
        description="Current ventilator setting",
        pattern="^(auto|minontime|on|off)$"
    )

    current_climate: str = Field(
        ...,
        description="Current climate/comfort setting",
        pattern="^(home|away|sleep|custom)$"
    )

    # Equipment stages (common in ecobee systems)
    heat_stage: Optional[int] = Field(
        None,
        description="Current heating stage (0 = off, 1 = stage 1, 2 = stage 2)",
        ge=0,
        le=2
    )

    cool_stage: Optional[int] = Field(
        None,
        description="Current cooling stage (0 = off, 1 = stage 1, 2 = stage 2)",
        ge=0,
        le=2
    )

    # Remote sensor summary
    connected_sensors: int = Field(
        0,
        description="Number of connected remote sensors",
        ge=0
    )

    average_temperature: Optional[float] = Field(
        None,
        description="Average temperature across all sensors in Celsius"
    )

    @field_validator('device_id')
    @classmethod
    def validate_device_id(cls, value: str) -> str:
        """Validate ecobee device identifier format"""
        if not value.isalnum():
            raise ValueError("Ecobee device identifier must be alphanumeric")
        return value

    @field_validator('average_temperature')
    @classmethod
    def validate_avg_temperature(cls, value: Optional[float]) -> Optional[float]:
        """Validate average temperature is within reasonable bounds"""
        if value is not None and not -50.0 <= value <= 100.0:
            raise ValueError("Average temperature must be between -50°C and 100°C")
        return value

    class Config:
        """Configuration and example data for the ecobee ambient data model"""
        json_schema_extra = {
            "example": {
                # Include all base ThermostatSensorData fields
                **ThermostatSensorData.Config.json_schema_extra["example"],
                # Add ecobee-specific fields
                "device_id": "123ABC456DEF",
                "device_name": "Main Floor",
                "aux_heat_active": False,
                "dehumidifier_mode": "auto",
                "ventilator_mode": "auto",
                "current_climate": "home",
                "heat_stage": 1,
                "cool_stage": 0,
                "connected_sensors": 3,
                "average_temperature": 22.5,
                # Override source to specify ecobee
                "source": "ecobee"
            }
        }

def main():
    """This allows testing the data model"""
    EcobeeAmbientData.test_model_main()

if __name__ == '__main__':
    main()