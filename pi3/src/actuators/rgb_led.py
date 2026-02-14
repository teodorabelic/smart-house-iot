from threading import Lock

try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None


class RGBLed:
    def __init__(self, pins, simulate=False):
        self.pins = pins
        self.simulate = simulate
        self.lock = Lock()
        self.pwm = {}

    def initialize(self):
        if self.simulate or GPIO is None:
            return
        for ch in ['red', 'green', 'blue']:
            pin = self.pins[ch]
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, 500)
            pwm.start(0)
            self.pwm[ch] = pwm

    def set_color(self, r, g, b):
        with self.lock:
            if self.simulate or GPIO is None:
                return {'red': r, 'green': g, 'blue': b}
            self.pwm['red'].ChangeDutyCycle(max(0, min(100, r)))
            self.pwm['green'].ChangeDutyCycle(max(0, min(100, g)))
            self.pwm['blue'].ChangeDutyCycle(max(0, min(100, b)))
            return {'red': r, 'green': g, 'blue': b}
