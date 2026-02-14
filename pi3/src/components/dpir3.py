import threading
from datetime import datetime
from sensors.pir import PirSensor, run_pir_loop
from simulators.binary import run_binary_simulator


def run_dpir3(settings, threads, stop_event, batch_sender, pi_id, device_name):
    simulated = settings.get('simulate', False)
    interval = settings.get('interval', 1)
    def cb(value, code):
        batch_sender.enqueue({'_topic': f'smart_home/{pi_id}/sensor/{code}/data', 'device_name': device_name, 'component': code, 'value': int(bool(value)), 'simulated': simulated, 'timestamp': datetime.utcnow().isoformat()})
    if simulated:
        th = threading.Thread(target=run_binary_simulator, args=(interval, cb, stop_event, 'DPIR3', 0.2), daemon=True)
    else:
        sensor = PirSensor(settings['pin'])
        th = threading.Thread(target=run_pir_loop, args=(sensor, interval, cb, stop_event, 'DPIR3'), daemon=True)
    th.start(); threads.append(th)
