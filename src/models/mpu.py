from typing import (Any, ClassVar, Dict, Final, List, Mapping, Optional,
                    Sequence, Tuple)

from typing_extensions import Self
from viam.components.sensor import *
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import SensorReading, ValueTypes, struct_to_dict

import board
import busio
import adafruit_mpu6050


class Mpu(Sensor, EasyResource):
    # To enable debug-level logging, either run viam-server with the --debug option,
    # or configure your resource/machine to display debug logs.
    MODEL: ClassVar[Model] = Model(ModelFamily("edss", "rocket-sensors"), "mpu-sensor")

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

        # Validate i2c_address parameter if provided
        if "i2c_address" in fields:
            if not fields["i2c_address"].HasField("number_value"):
                raise ValueError("i2c_address must be a valid number")
            else:
                i2c_address = int(fields["i2c_address"].number_value)
                if not (0x08 <= i2c_address <= 0x77):
                    raise ValueError("i2c_address must be a valid I2C address (0x08-0x77)")
        
        # Validate units parameter if provided
        if "units" in fields:
            if not fields["units"].HasField("string_value"):
                raise ValueError("units must be a valid string")
            else:
                units = fields["units"].string_value.lower()
                if units not in ["metric", "imperial"]:
                    raise ValueError("units must be either 'metric' or 'imperial'")
        
        # Validate sample_rate parameter if provided
        if "sample_rate" in fields:
            if not fields["sample_rate"].HasField("number_value"):
                raise ValueError("sample_rate must be a valid number")
            else:
                sample_rate = int(fields["sample_rate"].number_value)
                if sample_rate <= 0:
                    raise ValueError("sample_rate must be a positive number")
        
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
            # Initialize I2C and MPU sensor
            i2c = busio.I2C(board.SCL, board.SDA)
            
            attrs = struct_to_dict(config.attributes)
            self.i2c_address = int(attrs.get("i2c_address", 0x68))  # Default MPU6050 address
            self.units = attrs.get("units", "metric").lower()  # Default to metric units
            self.sample_rate = int(attrs.get("sample_rate", 100))  # Default 100Hz sample rate
            
            # Initialize MPU sensor
            self.sensor = adafruit_mpu6050.MPU6050(i2c, address=self.i2c_address)
            
            # Configure sensor settings
            self.sensor.accelerometer_range = adafruit_mpu6050.Range.RANGE_4_G
            self.sensor.gyro_range = adafruit_mpu6050.GyroRange.RANGE_500_DPS
            
            # Initialize tare offsets (default to 0 - no offset)
            self.accel_x_offset = 0.0
            self.accel_y_offset = 0.0
            self.accel_z_offset = 0.0
            self.gyro_x_offset = 0.0
            self.gyro_y_offset = 0.0
            self.gyro_z_offset = 0.0

        except Exception as e:
            self.logger.error(f"Failed to initialize IMU sensor: {e}")
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
                acceleration = self.sensor.acceleration  # (x, y, z) in m/s²
                gyro = self.sensor.gyro  # (x, y, z) in rad/s
                temperature = self.sensor.temperature  # in Celsius
                
                # Apply tare offsets (always applied, defaults to 0)
                accel_x = acceleration[0] - self.accel_x_offset
                accel_y = acceleration[1] - self.accel_y_offset
                accel_z = acceleration[2] - self.accel_z_offset
                
                gyro_x = gyro[0] - self.gyro_x_offset
                gyro_y = gyro[1] - self.gyro_y_offset
                gyro_z = gyro[2] - self.gyro_z_offset
                
                # Convert units based on configuration
                if self.units == "imperial":
                    # Convert acceleration from m/s² to ft/s²
                    accel_x_display = accel_x * 3.28084
                    accel_y_display = accel_y * 3.28084
                    accel_z_display = accel_z * 3.28084
                    accel_unit = "ft/s²"
                    
                    # Convert gyro from rad/s to deg/s
                    gyro_x_display = gyro_x * 57.2958  # rad to deg
                    gyro_y_display = gyro_y * 57.2958
                    gyro_z_display = gyro_z * 57.2958
                    gyro_unit = "deg/s"
                    
                    # Convert temperature from Celsius to Fahrenheit
                    temp_display = (temperature * 9/5) + 32
                    temp_unit = "F"
                else:  # metric (default)
                    accel_x_display = accel_x
                    accel_y_display = accel_y
                    accel_z_display = accel_z
                    accel_unit = "m/s²"
                    gyro_x_display = gyro_x
                    gyro_y_display = gyro_y
                    gyro_z_display = gyro_z
                    gyro_unit = "rad/s"
                    temp_display = temperature
                    temp_unit = "C"
                
                # Core MPU readings - 3 acceleration + 3 rotation speed + temperature
                readings = {
                    # 3-axis acceleration readings
                    f"acceleration_x - {accel_unit}": float(accel_x_display),
                    f"acceleration_y - {accel_unit}": float(accel_y_display),
                    f"acceleration_z - {accel_unit}": float(accel_z_display),
                    
                    # 3-axis gyroscope (rotation speed) readings
                    f"gyro_x - {gyro_unit}": float(gyro_x_display),
                    f"gyro_y - {gyro_unit}": float(gyro_y_display),
                    f"gyro_z - {gyro_unit}": float(gyro_z_display),
                    
                    # Temperature reading
                    f"temperature - {temp_unit}": float(temp_display),
                }
                
                return readings
            except Exception as e:
                self.logger.error(f"Error reading sensor data: {e}")
                return {}
        else:
            self.logger.error("Sensor not initialized")
            return {}

    async def tare(self):
        """Tare the IMU sensor by setting the current readings as baseline offsets."""
        if not self.sensor:
            self.logger.error("Sensor not initialized")
            raise RuntimeError("Sensor not initialized")
        
        try:
            self.logger.debug("Taring IMU sensor")
            # Read current values and set as baseline (offset = 0)
            acceleration = self.sensor.acceleration
            gyro = self.sensor.gyro
            
            self.accel_x_offset = acceleration[0]
            self.accel_y_offset = acceleration[1]
            self.accel_z_offset = acceleration[2]
            self.gyro_x_offset = gyro[0]
            self.gyro_y_offset = gyro[1]
            self.gyro_z_offset = gyro[2]
            
            self.logger.info(f"Tare set - Accel baseline: ({self.accel_x_offset:.3f}, {self.accel_y_offset:.3f}, {self.accel_z_offset:.3f}) m/s²")
            self.logger.info(f"Tare set - Gyro baseline: ({self.gyro_x_offset:.3f}, {self.gyro_y_offset:.3f}, {self.gyro_z_offset:.3f}) rad/s")
        except Exception as e:
            self.logger.error(f"Error during tare operation: {e}")
            raise

    async def reset_tare(self):
        """Reset tare offsets to zero."""
        try:
            self.logger.debug("Resetting tare offsets")
            self.accel_x_offset = 0.0
            self.accel_y_offset = 0.0
            self.accel_z_offset = 0.0
            self.gyro_x_offset = 0.0
            self.gyro_y_offset = 0.0
            self.gyro_z_offset = 0.0
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
                    "accel_x_offset": float(self.accel_x_offset),
                    "accel_y_offset": float(self.accel_y_offset),
                    "accel_z_offset": float(self.accel_z_offset),
                    "gyro_x_offset": float(self.gyro_x_offset),
                    "gyro_y_offset": float(self.gyro_y_offset),
                    "gyro_z_offset": float(self.gyro_z_offset)
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