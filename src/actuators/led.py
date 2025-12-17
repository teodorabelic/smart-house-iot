try:
    import RPi.GPIO as GPIO
except:
    GPIO = None

class Led:
    def __init__(self, pin: int):
        self.pin = pin

    def setup(self):
        if GPIO is None: return
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

    def on(self):
        if GPIO is None: return
        GPIO.output(self.pin, True)

    def off(self):
        if GPIO is None: return
        GPIO.output(self.pin, False)

    def toggle(self):
        if GPIO is None: return
        GPIO.output(self.pin, not GPIO.input(self.pin))
