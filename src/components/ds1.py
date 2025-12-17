import threading
import time
from src.simulators.binary import run_binary_simulator
from src.sensors.button import run_button_loop, ButtonSensor

def ds1_callback(value, code):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Pressed: {value}")

def run_ds1(settings, threads, stop_event):
    interval = settings.get("interval", 1)

    if settings["simulated"]:
        print("Starting DS1 simulator")
        th = threading.Thread(
            target=run_binary_simulator,
            args=(interval, ds1_callback, stop_event, "DS1", 0.15),
            daemon=True
        )
        th.start()
        threads.append(th)
    else:
        print("Starting DS1 real loop")
        sensor = ButtonSensor(settings["pin"], pull=settings.get("pull", "UP"))
        th = threading.Thread(
            target=run_button_loop,
            args=(sensor, interval, ds1_callback, stop_event, "DS1"),
            daemon=True
        )
        th.start()
        threads.append(th)
