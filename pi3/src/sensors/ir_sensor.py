try:
    import RPi.GPIO as GPIO
except Exception:
    GPIO = None


class IRSensor:
    def __init__(self, pin):
        self.pin = pin

    def setup(self):
        if GPIO is not None:
            GPIO.setup(self.pin, GPIO.IN)

    def read(self):
        if GPIO is None:
            return 0
        return GPIO.input(self.pin)
