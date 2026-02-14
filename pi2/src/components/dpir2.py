import threading
from datetime import datetime
from sensors.pir import PirSensor, run_pir_loop
from simulators.binary import run_binary_simulator


def run_dpir2(settings, threads, stop_event, batch_sender, pi_id, device_name):
    interval = settings.get('interval', 1)
    simulated = settings.get('simulate', False)

    def callback(value, code):
        batch_sender.enqueue({'_topic': f'smart_home/{pi_id}/sensor/{code}/data', 'device_name': device_name, 'component': code, 'value': int(bool(value)), 'simulated': simulated, 'timestamp': datetime.utcnow().isoformat()})

    if simulated:
        th = threading.Thread(target=run_binary_simulator, args=(interval, callback, stop_event, 'DPIR2', 0.2), daemon=True)
    else:
        sensor = PirSensor(settings['pin'])
        th = threading.Thread(target=run_pir_loop, args=(sensor, interval, callback, stop_event, 'DPIR2'), daemon=True)
    th.start(); threads.append(th)
