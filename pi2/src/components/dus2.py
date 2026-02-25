import threading
from datetime import datetime
from sensors.uds import UdsSensor, run_uds_loop
from simulators.uds import run_uds_simulator


def run_dus2(settings, threads, stop_event, batch_sender, pi_id, device_name):
    interval = settings.get('interval', 1)
    simulated = settings.get('simulate', False)

    def callback(value, code):
        batch_sender.enqueue({
            '_topic': f'smarthome/{pi_id}/sensors/{code}',
            'pi_id': pi_id,
            'device_name': device_name,
            'code': code,
            'value': float(value),
            'simulated': simulated,
            'ts': datetime.utcnow().isoformat(),
        })

    if simulated:
        th = threading.Thread(target=run_uds_simulator, args=(interval, callback, stop_event, 'DUS2'), daemon=True)
    else:
        sensor = UdsSensor(settings['trigger_pin'], settings['echo_pin'])
        th = threading.Thread(target=run_uds_loop, args=(sensor, interval, callback, stop_event, 'DUS2'), daemon=True)
    th.start(); threads.append(th)
