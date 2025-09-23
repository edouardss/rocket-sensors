import asyncio
from viam.module.module import Module

try:
    from models.mpu import Mpu
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.mpu import Mpu
    print("Could not find the module Mpu, locally")

try:
    from models.bmp import BmpSensor
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.bmp import BmpSensor
    print("Could not find the module BmpSensor, locally")

try:
    from models.loadcell import LoadCell
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.loadcell import LoadCell
    print("Could not find the module LoadCell, locally")

if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
