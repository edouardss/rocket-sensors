# Rocket Sensor Module

This module provides sensor components for the HX711 ADC with load cell for weight measurement, BMP sensor for atmospheric pressure and altitude measurement, and IMU sensor for motion sensing.

## Models

### 1. HX711 Loadcell Sensor

Module for supporting the HX711 ADC for use with a load cell to measure weight.

The loadcell model uses the hx711 Python library and is set to take the specified number of readings and return the average value of those readings.

#### Configuration for HX711

The following attribute template can be used to configure this model:

```json
{
  "gain": 64,
  "doutPin": 5,
  "sckPin": 6,
  "numberOfReadings": 3,
  "tare_offset": 0.0
}
```

#### Attributes

The following attributes are available for this model:

| Name | Type | Inclusion | Description |
|------|------|-----------|-------------|
| `gain` | float | Optional | Gain for hx711 readings (32, 64, or 128) |
| `doutPin` | int | Optional | GPIO pin for data out (1-40) |
| `sckPin` | int | Optional | GPIO pin for clock (1-40) |
| `numberOfReadings` | int | Optional | Number of readings to take each time (1-99) |
| `tare_offset` | float | Optional | Offset value to subtract from readings (must be ≤ 0) |

#### Example Configuration

```json
{
  "gain": 64,
  "doutPin": 5,
  "sckPin": 6,
  "numberOfReadings": 3,
  "tare_offset": 0.0
}
```

#### Commands

The `tare` function is a DoCommand. Call it with `"tare": {}`, the return value is the value (in kgs) of the weight that will be systematically subtracted from the readings.

### 2. BMP Altitude Sensor

BMP sensor for measuring atmospheric pressure and altitude.
Based on the delta between sea level pressure and current pressure.

#### Configuration
The following attribute template can be used to configure this model:

```json
{
  "sea_level_pressure": <int> (integer number given in Pa. Default value is 101325)
  "units": "metric" or "imperial" (default is "metric" - C, Pa and m. "imperial" is F, inHg, ft)
}
```

#### Attributes

The following attributes are available for this model:

| Name                 | Type  | Inclusion | Description                                    |
|----------------------|-------|-----------|------------------------------------------------|
| `sea_level_pressure` | int | Optional  | Sea level pressure in Pa for altitude calculations (default: 101325) |
| `units`              | string| Optional | metric or imperial units, default is metric |

#### Example Configuration

```json
{
  "sea_level_pressure": 101325,
  "units": "metric"
}
```

#### DoCommand

There is a command to `tare` the sensor to the current altitude, which returns current readings and sets offsets so that readings will subtract those values from pressure and altitude going forward. 
There is also a command `reset_tare` to reset the offset values to 0. 

#### Example DoCommand

```json
{
  "tare": {}
}
```

### 3. IMU Sensor

IMU sensor for measuring acceleration, gyroscope, and temperature using MPU6050/MPU9250 series sensors.

#### Configuration

The following attribute template can be used to configure this model:

```json
{
  "i2c_address": 104 (integer I2C address in decimal. Default value is 104 (0x68))
  "units": "metric" or "imperial" (default is "metric" - m/s², rad/s, C. "imperial" is ft/s², deg/s, F)
  "sample_rate": 100 (integer sample rate in Hz, default is 100)
}
```

#### Attributes

The following attributes are available for this model:

| Name | Type | Inclusion | Description |
|------|------|-----------|-------------|
| `i2c_address` | int | Optional | I2C address of the IMU sensor (default: 104/0x68) |
| `units` | string | Optional | metric or imperial units, default is metric |
| `sample_rate` | int | Optional | Sample rate in Hz (default: 100) |

#### Example Configuration

```json
{
  "i2c_address": 104,
  "units": "metric",
  "sample_rate": 100
}
```

#### DoCommand

There is a command to `tare` the sensor to the current orientation, which returns current readings and sets offsets so that readings will subtract those values from acceleration and gyroscope going forward. 
There is also a command `reset_tare` to reset the offset values to 0.

#### Example DoCommand

```json
{
  "tare": {}
}
```

## Installation

This module requires the following Python packages:
- `hx711` - for HX711 ADC communication
- `RPi.GPIO` - for GPIO control on Raspberry Pi
- `Adafruit_BMP` - for BMP sensor communication
- `adafruit-circuitpython-mpu6050` - for IMU sensor communication
- `board` and `busio` - for I2C communication

## Hardware Requirements

### HX711 Loadcell
- HX711 ADC module
- Load cell (strain gauge)
- Raspberry Pi or compatible single-board computer
- Jumper wires for connections

### BMP Sensor
- BMP085/BMP180/BMP280 sensor module
- I2C connection to Raspberry Pi
- 3.3V power supply

### IMU Sensor
- MPU6050/MPU9250 sensor module
- I2C connection to Raspberry Pi
- 3.3V power supply

## Usage

All sensors implement the Viam sensor interface and can be used with the Viam SDK. The sensors return readings as dictionaries with appropriate units (kg for weight, Pa for pressure, m for altitude, m/s² for acceleration, rad/s for gyroscope).
