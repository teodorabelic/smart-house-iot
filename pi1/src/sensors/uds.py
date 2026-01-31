import time

try:
    import RPi.GPIO as GPIO
except:
    GPIO = None

class UdsSensor:
    def __init__(self, trig_pin: int, echo_pin: int):
        self.trig = trig_pin
        self.echo = echo_pin

    def setup(self):
        if GPIO is None:
            return
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)
        GPIO.output(self.trig, False)
        time.sleep(0.05)

    def get_distance_cm(self):
        if GPIO is None:
            return None

        GPIO.output(self.trig, False)
        time.sleep(0.2)

        GPIO.output(self.trig, True)
        time.sleep(0.00001)
        GPIO.output(self.trig, False)

        pulse_start = time.time()
        pulse_end = time.time()

        max_iter = 100
        i = 0
        while GPIO.input(self.echo) == 0:
            if i > max_iter:
                return None
            pulse_start = time.time()
            i += 1

        i = 0
        while GPIO.input(self.echo) == 1:
            if i > max_iter:
                return None
            pulse_end = time.time()
            i += 1

        duration = pulse_end - pulse_start
        return round((duration * 34300) / 2, 2)

def run_uds_loop(sensor: UdsSensor, interval_sec, callback, stop_event, code):
    sensor.setup()
    while not stop_event.is_set():
        callback(sensor.get_distance_cm(), code)
        time.sleep(interval_sec)
