import threading
from datetime import datetime
from sensors.gyroscope import GyroscopeSensor
from simulators.gyro import GyroscopeSimulator


def run_gyro(settings, threads, stop_event, batch_sender, pi_id, device_name):
    simulated = settings.get('simulate', False)
    interval = settings.get('interval', 1)
    threshold = float(settings.get('threshold', 10.0))
    sensor = GyroscopeSimulator() if simulated else GyroscopeSensor(settings.get('i2c_address', '0x68'))

    def loop():
        while not stop_event.is_set():
            data = sensor.read()
            magnitude = abs(data['x']) + abs(data['y']) + abs(data['z'])
            data['significant_movement'] = magnitude >= threshold
            batch_sender.enqueue({
                '_topic': f'smarthome/{pi_id}/sensors/GSG',
                'pi_id': pi_id,
                'device_name': device_name,
                'code': 'GSG',
                'value': data,
                'simulated': simulated,
                'ts': datetime.utcnow().isoformat(),
            })
            stop_event.wait(interval)

    th = threading.Thread(target=loop, daemon=True)
    th.start(); threads.append(th)
