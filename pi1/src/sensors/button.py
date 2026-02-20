import time

try:
    import RPi.GPIO as GPIO
except:
    GPIO = None

class ButtonSensor:
    def __init__(self, pin: int, pull="UP"):
        self.pin = pin
        self.pull = (pull or "UP").upper()

    def setup(self):
        if GPIO is None:
            return
        if self.pull == "UP":
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif self.pull == "DOWN":
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        else:
            GPIO.setup(self.pin, GPIO.IN)

    def read_pressed(self) -> bool:
        if GPIO is None:
            return False
        v = GPIO.input(self.pin)
        if self.pull == "UP":
            return v == 0
        if self.pull == "DOWN":
            return v == 1
        return bool(v)

def run_button_loop(sensor: ButtonSensor, interval_sec, callback, stop_event, code):
    sensor.setup()
    last_state = None

    while not stop_event.is_set():
        current = sensor.read_pressed()

        if current != last_state:
            callback(current, code)
            last_state = current

        time.sleep(interval_sec)

