import threading
import time
from src.simulators.binary import run_binary_simulator
from src.sensors.pir import run_pir_loop, PirSensor

def dpir1_callback(value, code):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Motion: {value}")

def run_dpir1(settings, threads, stop_event):
    interval = settings.get("interval", 1)

    if settings["simulated"]:
        print("Starting DPIR1 simulator")
        th = threading.Thread(
            target=run_binary_simulator,
            args=(interval, dpir1_callback, stop_event, "DPIR1", 0.10),
            daemon=True
        )
        th.start()
        threads.append(th)
    else:
        print("Starting DPIR1 real loop")
        sensor = PirSensor(settings["pin"])
        th = threading.Thread(
            target=run_pir_loop,
            args=(sensor, interval, dpir1_callback, stop_event, "DPIR1"),
            daemon=True
        )
        th.start()
        threads.append(th)
