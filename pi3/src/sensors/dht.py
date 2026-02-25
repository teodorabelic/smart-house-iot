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
            
            try:
                temp = self.device.temperature
                hum = self.device.humidity
                if temp is not None and hum is not None:
                    self.last_read = time.time()
                    return {'temperature': temp, 'humidity': hum}
            except Exception:
                return {'temperature': None, 'humidity': None}
            return {'temperature': None, 'humidity': None}

    def cleanup(self):
        if hasattr(self, 'device') and self.device:
            self.device.exit()