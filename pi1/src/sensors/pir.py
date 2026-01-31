import time

try:
    import RPi.GPIO as GPIO
except:
    GPIO = None

class PirSensor:
    def __init__(self, pin: int):
        self.pin = pin

    def setup(self):
        if GPIO is None:
            return
        GPIO.setup(self.pin, GPIO.IN)

    def read_motion(self) -> bool:
        if GPIO is None:
            return False
        return bool(GPIO.input(self.pin))

def run_pir_loop(sensor: PirSensor, interval_sec, callback, stop_event, code):
    sensor.setup()
    while not stop_event.is_set():
        callback(sensor.read_motion(), code)
        time.sleep(interval_sec)
