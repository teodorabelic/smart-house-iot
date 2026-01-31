import threading
import time
from datetime import datetime
from simulators.binary import run_binary_simulator
from sensors.pir import run_pir_loop, PirSensor

def make_dpir1_callback(batch_sender, pi_id, device_name, simulated):
    def dpir1_callback(value, code):
        t = time.localtime()
        print("=" * 20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Motion: {value}")

        batch_sender.enqueue({
            "_topic": f"smarthome/{pi_id}/sensors/{code}",
            "pi_id": pi_id,
            "device_name": device_name,
            "code": code,
            "value": value,
            "simulated": simulated,
            "ts": datetime.utcnow().isoformat()
        })
    return dpir1_callback


def run_dpir1(settings, threads, stop_event, batch_sender, pi_id, device_name):
    interval = settings.get("interval", 1)
    simulated = settings.get("simulated", True)

    callback = make_dpir1_callback(batch_sender, pi_id, device_name, simulated)

    if simulated:
        print("Starting DPIR1 simulator")
        th = threading.Thread(
            target=run_binary_simulator,
            args=(interval, callback, stop_event, "DPIR1", 0.10),
            daemon=True
        )
    else:
        print("Starting DPIR1 real loop")
        sensor = PirSensor(settings["pin"])
        th = threading.Thread(
            target=run_pir_loop,
            args=(sensor, interval, callback, stop_event, "DPIR1"),
            daemon=True
        )

    th.start()
    threads.append(th)
