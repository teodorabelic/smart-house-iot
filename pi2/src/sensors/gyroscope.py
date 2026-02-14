from threading import Lock
from mpu6050 import mpu6050


class GyroscopeSensor:
    def __init__(self, i2c_address='0x68'):
        self.lock = Lock()
        self.sensor = mpu6050(int(i2c_address, 16) if isinstance(i2c_address, str) else int(i2c_address))

    def read(self):
        with self.lock:
            gyro = self.sensor.get_gyro_data()
            return {'x': gyro['x'], 'y': gyro['y'], 'z': gyro['z']}
