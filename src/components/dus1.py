import threading
import time
from src.simulators.uds import run_uds_simulator
from src.sensors.uds import run_uds_loop, UdsSensor

def dus1_callback(distance_cm, code):
    t = time.localtime()
    print("=" * 20)
    print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
    print(f"Code: {code}")
    print(f"Distance: {distance_cm} cm")

def run_dus1(settings, threads, stop_event):
    interval = settings.get("interval", 1)

    if settings["simulated"]:
        print("Starting DUS1 simulator")
        th = threading.Thread(
            target=run_uds_simulator,
            args=(interval, dus1_callback, stop_event, "DUS1"),
            daemon=True
        )
        th.start()
        threads.append(th)
    else:
        print("Starting DUS1 real loop")
        sensor = UdsSensor(settings["trig_pin"], settings["echo_pin"])
        th = threading.Thread(
            target=run_uds_loop,
            args=(sensor, interval, dus1_callback, stop_event, "DUS1"),
            daemon=True
        )
        th.start()
        threads.append(th)
