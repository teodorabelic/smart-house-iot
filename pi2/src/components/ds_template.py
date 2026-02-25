import threading
from datetime import datetime
from sensors.button import ButtonSensor, run_button_loop
from simulators.binary import run_binary_simulator


def run_button_component(code, settings, threads, stop_event, batch_sender, pi_id, device_name):
    interval = settings.get('interval', 1)
    simulated = settings.get('simulated', False)

    def callback(value, c):
        print(f"[{pi_id}] {c} value={bool(value)} simulated={simulated}")
        batch_sender.enqueue({
            '_topic': f'smarthome/{pi_id}/sensors/{c}',
            'pi_id': pi_id,
            'device_name': device_name,
            'code': c,
            'value': bool(value),
            'simulated': simulated,
            'ts': datetime.utcnow().isoformat(),
        })

    if simulated:
        th = threading.Thread(target=run_binary_simulator, args=(interval, callback, stop_event, code, 0.1), daemon=True)
    else:
        sensor = ButtonSensor(settings['pin'], pull='UP' if settings.get('pull_up', True) else 'NONE')
        th = threading.Thread(target=run_button_loop, args=(sensor, interval, callback, stop_event, code), daemon=True)
    th.start()
    threads.append(th)
