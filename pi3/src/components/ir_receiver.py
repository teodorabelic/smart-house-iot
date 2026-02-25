import threading
from datetime import datetime
from sensors.ir_sensor import IRSensor
from simulators.ir import IRSimulator


def run_ir_receiver(settings, threads, stop_event, batch_sender, pi_id, device_name, on_command):
    simulated = settings.get('simulate', False)
    interval = settings.get('interval', 0.5)
    sensor = IRSimulator() if simulated else IRSensor(settings['pin'])
    if not simulated:
        sensor.setup()

    def loop():
        while not stop_event.is_set():
            raw = sensor.read()
            cmd = raw if isinstance(raw, str) else ('POWER' if raw else 'NONE')
            if cmd != 'NONE':
                on_command(cmd)
                batch_sender.enqueue({
                    '_topic': f'smarthome/{pi_id}/sensors/IR',
                    'pi_id': pi_id,
                    'device_name': device_name,
                    'code': 'IR',
                    'value': cmd,
                    'simulated': simulated,
                    'ts': datetime.utcnow().isoformat(),
                })
            stop_event.wait(interval)

    th = threading.Thread(target=loop, daemon=True)
    th.start(); threads.append(th)
