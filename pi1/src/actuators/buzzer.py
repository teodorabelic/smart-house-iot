import time
try:
    import RPi.GPIO as GPIO
except:
    GPIO = None

class Buzzer:
    def __init__(self, pin: int):
        self.pin = pin
        self.pwm = None

    def setup(self):
        if GPIO is None: return
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)
        self.pwm = GPIO.PWM(self.pin, 440)

    def on(self, pitch=440):
        if self.pwm is None: return
        self.pwm.ChangeFrequency(int(pitch))
        self.pwm.start(50)

    def off(self):
        if self.pwm is None: return
        self.pwm.stop()
        GPIO.output(self.pin, False)

    def beep(self, n=1, duration=0.2, pitch=440):
        if self.pwm is None: return
        for _ in range(int(n)):
            self.on(pitch)
            time.sleep(float(duration))
            self.off()
            time.sleep(float(duration))

    def state(self) -> bool:
        return self._on