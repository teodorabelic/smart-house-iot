import threading
import time
from datetime import datetime
from simulators.binary import run_binary_simulator
from sensors.button import run_button_loop, ButtonSensor

def make_ds1_callback(batch_sender, pi_id, device_name, simulated):
    def ds1_callback(value, code):
        t = time.localtime()
        print("=" * 20)
        print(f"Timestamp: {time.strftime('%H:%M:%S', t)}")
        print(f"Code: {code}")
        print(f"Pressed: {value}")

        batch_sender.enqueue({
            "_topic": f"smarthome/{pi_id}/sensors/{code}",
            "pi_id": pi_id,
            "device_name": device_name,
            "code": code,
            "value": value,
            "simulated": simulated,
            "ts": datetime.utcnow().isoformat()
        })
    return ds1_callback


def run_ds1(settings, threads, stop_event, batch_sender, pi_id, device_name):
    interval = settings.get("interval", 1)
    simulated = settings.get("simulated", True)

    callback = make_ds1_callback(batch_sender, pi_id, device_name, simulated)

    if simulated:
        print("Starting DS1 simulator")
        th = threading.Thread(
            target=run_binary_simulator,
            args=(interval, callback, stop_event, "DS1", 0.15),
            daemon=True
        )
    else:
        print("Starting DS1 real loop")
        sensor = ButtonSensor(settings["pin"], pull=settings.get("pull", "UP"))
        th = threading.Thread(
            target=run_button_loop,
            args=(sensor, interval, callback, stop_event, "DS1"),
            daemon=True
        )

    th.start()
    threads.append(th)
