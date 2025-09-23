from typing import (Any, ClassVar, Mapping, Optional,Sequence)

from typing_extensions import Self
from viam.components.sensor import *
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import SensorReading, ValueTypes, struct_to_dict
import Adafruit_BMP.BMP085 as BMP085
import board
import busio

class BmpSensor(Sensor, EasyResource):
    # To enable debug-level logging, either run viam-server with the --debug option,
    # or configure your resource/machine to display debug logs.
    MODEL: ClassVar[Model] = Model(ModelFamily("edss", "rocket-sensors"), "bmp-sensor")
    # print('MODEL: ', Self.MODEL)

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """This method creates a new instance of this Sensor component.
        The default implementation sets the name from the `config` parameter and then calls `reconfigure`.

        Args:
            config (ComponentConfig): The configuration for this resource
            dependencies (Mapping[ResourceName, ResourceBase]): The dependencies (both implicit and explicit)

        Returns:
            Self: The resource
        """
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        """This method allows you to validate the configuration object received from the machine,
        as well as to return any implicit dependencies based on that `config`.

        Args:
            config (ComponentConfig): The configuration for this resource

        Returns:
            Sequence[str]: A list of implicit dependencies
        """
        fields = config.attributes.fields

        # Validate sea_level_pressure parameter if provided
        if "sea_level_pressure" in fields:
            if not(fields["sea_level_pressure"].HasField("number_value")):
                raise ValueError("sea_level_pressure must be a valid number")
            else:
                sea_level_pressure = int(fields["sea_level_pressure"].number_value)
                if sea_level_pressure <= 0:
                    raise ValueError("sea_level_pressure must be a positive number")
        
        # Validate units parameter if provided
        if "units" in fields:
            if not fields["units"].HasField("string_value"):
                raise ValueError("units must be a valid string")
            else:
                units = fields["units"].string_value.lower()
                if units not in ["metric", "imperial"]:
                    raise ValueError("units must be either 'metric' or 'imperial'")
        
        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """This method allows you to dynamically update your service when it receives a new `config` object.

        Args:
            config (ComponentConfig): The new configuration
            dependencies (Mapping[ResourceName, ResourceBase]): Any dependencies (both implicit and explicit)
        """
        try:
            # Initialize I2C and BMP sensor
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = BMP085.BMP085(busnum=1)
            
            attrs = struct_to_dict(config.attributes)
            self.sea_level_pressure = int(attrs.get("sea_level_pressure", 101325))  # Default sea level pressure in hPa*100
            self.units = attrs.get("units", "metric").lower()  # Default to metric units
            
            # Initialize tare offsets (default to 0 - no offset)
            self.pressure_offset = 0.0
            self.altitude_offset = 0.0

        except Exception as e:
            self.logger.error(f"Failed to initialize BMP sensor: {e}")
            self.sensor = None
            raise
 
        return super().reconfigure(config, dependencies)

    async def get_readings(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, SensorReading]:
        if self.sensor:
            try:
                # Read sensor data
                temperature = self.sensor.read_temperature()
                raw_pressure = self.sensor.read_pressure()
                raw_altitude = self.sensor.read_altitude(self.sea_level_pressure)
                
                # Apply tare offsets (always applied, defaults to 0)
                pressure = raw_pressure - self.pressure_offset
                altitude = raw_altitude - self.altitude_offset
                
                # Convert units based on configuration
                if self.units == "imperial":
                    # Convert temperature from Celsius to Fahrenheit
                    temperature_display = (temperature * 9/5) + 32
                    temp_unit = "F"
                    
                    # Convert pressure from Pa to inHg (inches of mercury)
                    pressure_display = pressure * 0.0002953  # Pa to inHg
                    pressure_unit = "inHg"
                    
                    # Convert altitude from meters to feet
                    altitude_display = altitude * 3.28084  # meters to feet
                    altitude_unit = "ft"
                    
                    # Convert sea level pressure
                    sea_level_display = self.sea_level_pressure * 0.0002953
                    sea_level_unit = "inHg"
                    
                    # Convert raw values
                    raw_pressure_display = raw_pressure * 0.0002953
                    raw_altitude_display = raw_altitude * 3.28084
                    
                    # Convert offsets
                    pressure_offset_display = self.pressure_offset * 0.0002953
                    altitude_offset_display = self.altitude_offset * 3.28084
                else:  # metric (default)
                    temperature_display = temperature
                    temp_unit = "C"
                    pressure_display = pressure
                    pressure_unit = "Pa"
                    altitude_display = altitude
                    altitude_unit = "m"
                    sea_level_display = self.sea_level_pressure
                    sea_level_unit = "Pa"
                    raw_pressure_display = raw_pressure
                    raw_altitude_display = raw_altitude
                    pressure_offset_display = self.pressure_offset
                    altitude_offset_display = self.altitude_offset
                
                readings = {
                    f"temperature - {temp_unit}": float(temperature_display),
                    f"pressure - {pressure_unit}": float(pressure_display),
                    f"altitude - {altitude_unit}": float(altitude_display),
                    f"sea_level_pressure - {sea_level_unit}": float(sea_level_display),
                    f"raw_pressure - {pressure_unit}": float(raw_pressure_display),
                    f"raw_altitude - {altitude_unit}": float(raw_altitude_display),
                    f"pressure_offset - {pressure_unit}": float(pressure_offset_display),
                    f"altitude_offset - {altitude_unit}": float(altitude_offset_display),
                }
                
                return readings
            except Exception as e:
                self.logger.error(f"Error reading sensor data: {e}")
                return {}
        else:
            self.logger.error("Sensor not initialized")
            return {}

    async def tare(self):
        """Tare the BMP sensor by setting the current readings as baseline offsets."""
        if not self.sensor:
            self.logger.error("Sensor not initialized")
            raise RuntimeError("Sensor not initialized")
        
        try:
            self.logger.debug("Taring BMP sensor")
            # Read current values and set as baseline (offset = 0)
            self.pressure_offset = self.sensor.read_pressure()
            self.altitude_offset = self.sensor.read_altitude(self.sea_level_pressure)
            
            self.logger.info(f"Tare set - Pressure baseline: {self.pressure_offset:.2f} Pa, Altitude baseline: {self.altitude_offset:.2f} m")
        except Exception as e:
            self.logger.error(f"Error during tare operation: {e}")
            raise

    async def reset_tare(self):
        """Reset tare offsets to zero."""
        try:
            self.logger.debug("Resetting tare offsets")
            self.pressure_offset = 0.0
            self.altitude_offset = 0.0
            self.logger.info("Tare reset - returning to raw readings")
        except Exception as e:
            self.logger.error(f"Error during reset tare operation: {e}")
            raise

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, ValueTypes]:
        result = {key: False for key in command.keys()}
        for name, args in command.items():
            if name == "tare":
                await self.tare(*args)
                result[name] = {
                    "pressure_offset": float(self.pressure_offset),
                    "altitude_offset": float(self.altitude_offset)
                }
            elif name == "reset_tare":
                await self.reset_tare(*args)
                result[name] = True
            else:
                result[name] = {
                    "error": f"Unknown command: {name}",
                    "available_commands": ["tare", "reset_tare"]
                }
        return result


