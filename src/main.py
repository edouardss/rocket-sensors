import asyncio
from viam.module.module import Module

try:
    from models.mpu import Mpu
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.mpu import Mpu

try:
    from models.loadcell import LoadCell
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.loadcell import LoadCell
    print("Could not find the module LoadCell, locally")

if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
