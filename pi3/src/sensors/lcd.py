from threading import Lock

try:
    from RPLCD.i2c import CharLCD
except Exception:
    CharLCD = None


class LCDDisplay:
    def __init__(self, address='0x27', cols=16, rows=2, simulate=False):
        self.simulate = simulate
        self.lock = Lock()
        self.cols = cols
        self.rows = rows
        self.device = None
        if not simulate and CharLCD is not None:
            self.device = CharLCD(i2c_expander='PCF8574', address=int(address, 16), cols=cols, rows=rows)

    def show(self, line1, line2=''):
        with self.lock:
            if self.device is not None:
                self.device.clear()
                self.device.write_string((line1 or '')[:self.cols])
                self.device.crlf()
                self.device.write_string((line2 or '')[:self.cols])
            return {'line1': line1, 'line2': line2}
