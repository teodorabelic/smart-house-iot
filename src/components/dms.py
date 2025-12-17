import threading
import time
from src.simulators.binary import run_binary_simulator
from src.sensors.button import run_button_loop, ButtonSensor

def dms_callback(value, code):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Pressed: {value}")

def run_dms(settings, threads, stop_event):
    interval = settings.get("interval", 1)

    if settings["simulated"]:
        print("Starting DMS simulator")
        th = threading.Thread(
            target=run_binary_simulator,
            args=(interval, dms_callback, stop_event, "DMS", 0.08),
            daemon=True
        )
        th.start()
        threads.append(th)
    else:
        print("Starting DMS real loop")
        sensor = ButtonSensor(settings["pin"], pull=settings.get("pull", "UP"))
        th = threading.Thread(
            target=run_button_loop,
            args=(sensor, interval, dms_callback, stop_event, "DMS"),
            daemon=True
        )
        th.start()
        threads.append(th)
