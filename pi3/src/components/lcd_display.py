import threading
from sensors.lcd import LCDDisplay


def run_lcd_display(settings, threads, stop_event, get_lines):
    lcd = LCDDisplay(settings.get('i2c_address', '0x27'), settings.get('cols', 16), settings.get('rows', 2), settings.get('simulated', False))
    interval = settings.get('rotation_interval', 5)

    def loop():
        while not stop_event.is_set():
            l1, l2 = get_lines()
            lcd.show(l1, l2)
            print(f"[PI3] LCD line1={l1} line2={l2} simulated={settings.get('simulated', False)}")
            stop_event.wait(interval)

    th = threading.Thread(target=loop, daemon=True)
    th.start(); threads.append(th)
