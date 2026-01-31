import threading
import time
from datetime import datetime
from simulators.binary import run_binary_simulator
from sensors.button import run_button_loop, ButtonSensor


def dms_callback(value, code, batch_sender, pi_id, device_name):
    t = datetime.utcnow().isoformat()

    print("=" * 20)
    print(f"Timestamp: {t}")
    print(f"Code: {code}")
    print(f"Pressed: {value}")

    batch_sender.enqueue({
        "_topic": f"smarthome/{pi_id}/sensors/{code}",
        "pi_id": pi_id,
        "device_name": device_name,
        "code": code,
        "value": bool(value),
        "simulated": True,
        "ts": t
    })


def run_dms(settings, threads, stop_event, batch_sender, pi_id, device_name):
    interval = settings.get("interval", 1)
    simulated = settings.get("simulated", True)

    if simulated:
        print("Starting DMS simulator")
        th = threading.Thread(
            target=run_binary_simulator,
            args=(
                interval,
                lambda v, c: dms_callback(v, c, batch_sender, pi_id, device_name),
                stop_event,
                "DMS",
                0.08
            ),
            daemon=True
        )
    else:
        print("Starting DMS real loop")
        sensor = ButtonSensor(settings["pin"], pull=settings.get("pull", "UP"))
        th = threading.Thread(
            target=run_button_loop,
            args=(
                sensor,
                interval,
                lambda v, c: dms_callback(v, c, batch_sender, pi_id, device_name),
                stop_event,
                "DMS"
            ),
            daemon=True
        )

    th.start()
    threads.append(th)
