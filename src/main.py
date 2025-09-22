import asyncio
from viam.module.module import Module

try:
    from models.mpu import Mpu
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.mpu import Mpu

if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
