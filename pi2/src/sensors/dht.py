import time
from threading import Lock
try:
    import board
    import adafruit_dht
except ImportError:
    board = None
    adafruit_dht = None

class DHT11Sensor:
    def __init__(self, pin):
        self.lock = Lock()
        self.device = adafruit_dht.DHT11(getattr(board, f'D{pin}'))
        self.last_read = 0

    def read(self):
        with self.lock:
            now = time.time()
            if now - self.last_read < 2:
                time.sleep(2 - (now - self.last_read))
            self.last_read = time.time()
            return {'temperature': self.device.temperature, 'humidity': self.device.humidity}

    def cleanup(self):
        self.device.exit()
