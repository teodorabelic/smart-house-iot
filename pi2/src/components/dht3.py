import threading
from datetime import datetime
from sensors.dht import DHT11Sensor
from simulators.dht import DHT11Simulator


def run_dht3(settings, threads, stop_event, batch_sender, pi_id, device_name):
    simulated = settings.get('simulate', False)
    interval = settings.get('read_interval', 5)
    sensor = DHT11Simulator() if simulated else DHT11Sensor(settings['pin'])

    def loop():
        while not stop_event.is_set():
            try:
                data = sensor.read()
                batch_sender.enqueue({
                    '_topic': f'smarthome/{pi_id}/sensors/DHT3',
                    'pi_id': pi_id,
                    'device_name': device_name,
                    'code': 'DHT3',
                    'value': data,
                    'simulated': simulated,
                    'ts': datetime.utcnow().isoformat(),
                })
            except Exception:
                pass
            stop_event.wait(interval)
        if hasattr(sensor, 'cleanup'):
            sensor.cleanup()

    th = threading.Thread(target=loop, daemon=True)
    th.start(); threads.append(th)
