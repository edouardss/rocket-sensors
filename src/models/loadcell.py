"""HX711 Load Cell sensor model implementation."""

from typing import Any, ClassVar, Mapping, Optional, Sequence

from typing_extensions import Self
from viam.components.sensor import Sensor
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import SensorReading, struct_to_dict, ValueTypes

# Handle RPi.GPIO import for non-Raspberry Pi systems (like GitHub Actions)
# This must be done BEFORE importing hx711, as hx711 also imports RPi.GPIO
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Create a comprehensive mock GPIO module for non-Raspberry Pi systems
    class MockGPIO:
        # GPIO constants
        OUT = 0
        IN = 1
        HIGH = 1
        LOW = 0
        BCM = 11
        BOARD = 10

        @staticmethod
        def cleanup(pins=None):
            pass  # No-op for testing/CI environments

        @staticmethod
        def setup(pin, mode, initial=None):
            pass  # No-op for testing/CI environments

        @staticmethod
        def output(pin, value):
            pass  # No-op for testing/CI environments

        @staticmethod
        def input(pin):
            return 0  # Return 0 for testing/CI environments

        @staticmethod
        def setmode(mode):
            pass  # No-op for testing/CI environments

        @staticmethod
        def setwarnings(flag):
            pass  # No-op for testing/CI environments

        @staticmethod
        def getmode():
            return MockGPIO.BCM  # Return BCM mode for testing/CI environments

    GPIO = MockGPIO
    # Mock RPi.GPIO at the module level so hx711 can import it
    import sys

    sys.modules["RPi"] = type(sys)("RPi")
    sys.modules["RPi.GPIO"] = GPIO

from hx711 import HX711


class LoadCell(Sensor, EasyResource):
    """HX711 Load Cell sensor implementation."""

    MODEL: ClassVar[Model] = Model(ModelFamily("edss", "rocket-sensors"), "loadcell")

    @classmethod
    def new(
        cls,
        config: ComponentConfig,
        dependencies: Mapping[ResourceName, ResourceBase],
    ) -> Self:
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        fields = config.attributes.fields
        errors = []

        # Validate gain: must be 32, 64, or 128
        if "gain" in fields:
            if not fields["gain"].HasField("number_value"):
                errors.append("Gain must be a valid number.")
            else:
                gain = fields["gain"].number_value
                if gain not in [32, 64, 128]:
                    errors.append("Gain must be 32, 64, or 128.")

        # Validate doutPin: must be a valid GPIO pin number (1-40 for Raspberry Pi)
        if "doutPin" in fields:
            if not fields["doutPin"].HasField("number_value"):
                errors.append("Data Out pin must be a valid number.")
            else:
                dout_pin = int(fields["doutPin"].number_value)
                if not (1 <= dout_pin <= 40):
                    errors.append(
                        "Data Out pin must be a valid GPIO pin number (1-40)."
                    )

        # Validate sckPin: must be a valid GPIO pin number (1-40 for Raspberry Pi)
        if "sckPin" in fields:
            if not fields["sckPin"].HasField("number_value"):
                errors.append("Clock pin must be a valid number.")
            else:
                sck_pin = int(fields["sckPin"].number_value)
                if not (1 <= sck_pin <= 40):
                    errors.append("Clock pin must be a valid GPIO pin number (1-40).")

        # Validate numberOfReadings: must be positive integer less than 100
        if "numberOfReadings" in fields:
            if not fields["numberOfReadings"].HasField("number_value"):
                errors.append("Number of readings must be a valid number.")
            else:
                num_readings = int(fields["numberOfReadings"].number_value)
                if not (1 <= num_readings < 100):
                    errors.append(
                        "Number of readings must be a positive integer less than 100."
                    )

        # Validate tare_offset: must be a negative floating point value
        if "tare_offset" in fields:
            if not fields["tare_offset"].HasField("number_value"):
                errors.append("Tare offset must be a valid number.")
            else:
                tare_offset = fields["tare_offset"].number_value
                if tare_offset > 0:
                    errors.append(
                        "Tare offset must be a non-positive floating point value (≤ 0.0)."
                    )

        # If there are validation errors, raise an exception with all errors
        if errors:
            raise Exception("; ".join(errors))

        return []

    def reconfigure(
        self,
        config: ComponentConfig,
        dependencies: Mapping[ResourceName, ResourceBase],
    ):
        attrs = struct_to_dict(config.attributes)
        self.gain = float(attrs.get("gain", 64))
        self.doutPin = int(attrs.get("doutPin", 5))
        self.sckPin = int(attrs.get("sckPin", 6))
        self.numberOfReadings = int(attrs.get("numberOfReadings", 3))
        self.tare_offset = float(attrs.get("tare_offset", 0.0))

        self.logger.debug(
            f"Reconfigured with gain {self.gain}, doutPin {self.doutPin}, "
            f"sckPin {self.sckPin}, numberOfReadings {self.numberOfReadings}, "
            f"tare_offset {self.tare_offset}"
        )

        # Initialize HX711 object if not already done
        if not hasattr(self, "hx711") or self.hx711 is None:
            self.hx711 = None
            self.get_hx711()

        return super().reconfigure(config, dependencies)

    def get_hx711(self):
        """Get the HX711 instance, creating it if necessary."""
        if self.hx711 is None:
            try:
                self.logger.debug(
                    f"Initializing HX711 with doutPin {self.doutPin}, sckPin {self.sckPin}, gain {self.gain}"
                )
                self.hx711 = HX711(
                    dout_pin=self.doutPin,
                    pd_sck_pin=self.sckPin,
                    channel="A",
                    gain=self.gain,
                )
                # Reset the HX711 only when first created
                self.hx711.reset()
                self.logger.debug("HX711 initialized and reset successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize HX711: {e}")
                # Clean up the failed object
                if hasattr(self, "hx711") and self.hx711 is not None:
                    try:
                        del self.hx711
                    except Exception as cleanup_error:
                        self.logger.warning(
                            f"Error cleaning up failed HX711 object: {cleanup_error}"
                        )
                self.hx711 = None
                raise
        return self.hx711

    def cleanup_gpio_pins(self):
        """Clean up only the specific GPIO pins used by this sensor."""
        try:
            self.logger.debug(f"Cleaning up GPIO pins {self.doutPin}, {self.sckPin}")
            GPIO.cleanup((self.doutPin, self.sckPin))
        except Exception as e:
            self.logger.warning(
                f"Error cleaning up GPIO pins {self.doutPin}, {self.sckPin}: {e}"
            )

    def close(self):
        """Clean up resources when the component is closed."""
        try:
            if hasattr(self, "hx711") and self.hx711 is not None:
                del self.hx711
                self.hx711 = None
            self.cleanup_gpio_pins()
            self.logger.debug("Load cell component closed and resources cleaned up")
        except Exception as e:
            self.logger.warning(f"Error during component cleanup: {e}")

    async def get_readings(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, SensorReading]:

        try:
            self.logger.debug("Getting readings from load cell")
            hx711 = self.get_hx711()
            measures = hx711.get_raw_data(times=self.numberOfReadings)
            # Convert each measure to kgs by subtracting tare offset and dividing by 8200
            measures_kg = [(measure - self.tare_offset) / 8200 for measure in measures]
            avg_kgs = sum(measures_kg) / len(
                measures_kg
            )  # Assuming 8200 ~ 1kg, then this converts to kg

            # Return a dictionary of the readings
            return {
                "doutPin": self.doutPin,
                "sckPin": self.sckPin,
                "gain": self.gain,
                "numberOfReadings": self.numberOfReadings,
                "tare_offset": self.tare_offset
                / 8200,  # reporting tare value in kgs for consistency with readings
                "measures": measures_kg,  # Now returning measures in kg
                "weight": avg_kgs,
            }
        except Exception as e:
            self.logger.error(f"Error getting readings from load cell: {e}")
            # If there's an error, clean up and reset the HX711 object for next time
            if hasattr(self, "hx711") and self.hx711 is not None:
                try:
                    del self.hx711
                except Exception as cleanup_error:
                    self.logger.warning(
                        f"Error cleaning up HX711 object after reading error: {cleanup_error}"
                    )
            self.hx711 = None
            raise

    async def tare(self):
        """Tare the load cell by setting the current reading as the zero offset."""

        try:
            self.logger.debug("Taring load cell")
            hx711 = self.get_hx711()
            measures = hx711.get_raw_data(times=self.numberOfReadings)
            self.tare_offset = sum(measures) / len(measures)  # Set tare offset
            self.logger.debug(f"Tare completed. New offset: {self.tare_offset}")
        except Exception as e:
            self.logger.error(f"Error during tare operation: {e}")
            # If there's an error, clean up and reset the HX711 object for next time
            if hasattr(self, "hx711") and self.hx711 is not None:
                try:
                    del self.hx711
                except Exception as cleanup_error:
                    self.logger.warning(
                        f"Error cleaning up HX711 object after tare error: {cleanup_error}"
                    )
            self.hx711 = None
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
                result[name] = self.tare_offset / 8200
        return result
