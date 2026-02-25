import threading
from datetime import datetime
from sensors.keypad import KeypadSensor, run_keypad_loop
from simulators.keypad import run_keypad_simulator

def dms_callback(key, code, batch_sender, pi_id, device_name, simulated):
    t = datetime.utcnow().isoformat()

    print("=" * 20)
    print(f"Timestamp: {t}")
    print(f"Code: {code}")
    print(f"Key pressed: {key}")

    batch_sender.enqueue({
        "_topic": f"smarthome/{pi_id}/sensors/{code}",
        "pi_id": pi_id,
        "device_name": device_name,
        "code": code,
        "value": key,
        "key": key,
        "simulated": simulated,
        "ts": t
    })


def run_dms(settings, threads, stop_event, batch_sender, pi_id, device_name):
    interval = settings.get("interval", 0.1)
    simulated = settings.get("simulated", True)

    if simulated:
        print("Starting Keypad simulator")
        cb = lambda key, code: dms_callback(
            key, code, batch_sender, pi_id, device_name, True
        )
        th = threading.Thread(
            target=run_keypad_simulator,
            args=(interval, cb, stop_event, "DMS"),
            daemon=True
        )
        th.start()
        threads.append(th)
        return

    print("Starting Keypad real loop")

    sensor = KeypadSensor(settings["rows"], settings["cols"])

    cb = lambda key, code: dms_callback(
        key, code, batch_sender, pi_id, device_name, False
    )

    th = threading.Thread(
        target=run_keypad_loop,
        args=(sensor, interval, cb, stop_event, "DMS"),
        daemon=True
    )

    th.start()
    threads.append(th)
