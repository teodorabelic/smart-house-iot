import threading
from datetime import datetime
from simulators.uds import run_uds_simulator
from sensors.uds import run_uds_loop, UdsSensor


def dus1_callback(distance_cm, code, batch_sender, pi_id, device_name, simulated):
    t = datetime.utcnow().isoformat()

    print("=" * 20)
    print(f"Timestamp: {t}")
    print(f"Code: {code}")
    print(f"Distance: {distance_cm} cm")

    batch_sender.enqueue({
        "_topic": f"smarthome/{pi_id}/sensors/{code}",
        "pi_id": pi_id,
        "device_name": device_name,
        "code": code,
        "value": float(distance_cm),
        "simulated": simulated,
        "ts": t
    })


def run_dus1(settings, threads, stop_event, batch_sender, pi_id, device_name):
    interval = settings.get("interval", 1)
    simulated = settings.get("simulated", True)

    cb = lambda v, c: dus1_callback(v, c, batch_sender, pi_id, device_name, simulated)

    if simulated:
        print("Starting DUS1 simulator")
        th = threading.Thread(
            target=run_uds_simulator,
            args=(interval, cb, stop_event, "DUS1"),
            daemon=True
        )
    else:
        print("Starting DUS1 real loop")
        sensor = UdsSensor(settings["trig_pin"], settings["echo_pin"])
        th = threading.Thread(
            target=run_uds_loop,
            args=(sensor, interval, cb, stop_event, "DUS1"),
            daemon=True
        )

    th.start()
    threads.append(th)
