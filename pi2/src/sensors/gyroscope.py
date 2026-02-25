from threading import Lock
try:
    from mpu6050 import mpu6050
except ImportError:
    mpu6050 = None


class GyroscopeSensor:
    def __init__(self, i2c_address='0x68'):
        if mpu6050 is None:
            raise ImportError("Biblioteka 'mpu6050' nije instalirana. Ovo se pokrece samo na Raspberry Piju.")
        
        self.lock = Lock()
        addr = int(i2c_address, 16) if isinstance(i2c_address, str) else int(i2c_address)
        self.sensor = mpu6050(addr)

    def read(self):
        with self.lock:
            gyro = self.sensor.get_gyro_data()
            return {'x': gyro['x'], 'y': gyro['y'], 'z': gyro['z']}