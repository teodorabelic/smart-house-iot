import time
try:
    import RPi.GPIO as GPIO
except:
    GPIO = None

KEY_MAP = [
    ["1","2","3","A"],
    ["4","5","6","B"],
    ["7","8","9","C"],
    ["*","0","#","D"]
]

class KeypadSensor:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def setup(self):
        if GPIO is None:
            return

        for r in self.rows:
            GPIO.setup(r, GPIO.OUT)
            GPIO.output(r, GPIO.HIGH)

        for c in self.cols:
            GPIO.setup(c, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read_key(self):
        if GPIO is None:
            return None

        for i, r in enumerate(self.rows):
            GPIO.output(r, GPIO.LOW)

            for j, c in enumerate(self.cols):
                if GPIO.input(c) == GPIO.LOW:
                    GPIO.output(r, GPIO.HIGH)
                    return KEY_MAP[i][j]

            GPIO.output(r, GPIO.HIGH)

        return None


def run_keypad_loop(sensor, interval, callback, stop_event, code):
    sensor.setup()
    last_key = None

    while not stop_event.is_set():
        key = sensor.read_key()

        if key and key != last_key:
            callback(key, code)
            last_key = key

        if not key:
            last_key = None

        time.sleep(interval)