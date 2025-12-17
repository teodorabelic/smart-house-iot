import threading
import time
from settings import load_settings

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except:
    GPIO = None

from components.ds1 import run_ds1
from components.dpir1 import run_dpir1
from components.dms import run_dms
from components.dus1 import run_dus1
from components.cli import run_cli


if __name__ == "__main__":
    print("Starting KT1 (PI1) app")

    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    try:
        # start sensor threads
        if "DS1" in settings:   run_ds1(settings["DS1"], threads, stop_event)
        if "DPIR1" in settings: run_dpir1(settings["DPIR1"], threads, stop_event)
        if "DMS" in settings:   run_dms(settings["DMS"], threads, stop_event)
        if "DUS1" in settings:  run_dus1(settings["DUS1"], threads, stop_event)

        # CLI (actuators control) in main thread
        run_cli(settings, stop_event)

    except KeyboardInterrupt:
        print("Stopping app (Ctrl+C)")
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=1.0)

        if GPIO is not None:
            try:
                GPIO.cleanup()
            except:
                pass

        print("Stopped.")
