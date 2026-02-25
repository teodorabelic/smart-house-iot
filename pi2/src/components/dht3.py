import threading
from datetime import datetime

from simulators.dht import DHT11Simulator


def run_dht3(settings, threads, stop_event, batch_sender, pi_id, device_name):
    simulated = settings.get('simulated', False)
    interval = settings.get('read_interval', 5)
    if simulated:
        sensor = DHT11Simulator()
    else:
        from sensors.dht import DHT11Sensor
        sensor = DHT11Sensor(settings['pin'])

    def loop():
        while not stop_event.is_set():
            try:
                data = sensor.read()
                print(f"[{pi_id}] DHT3 value={data} simulated={simulated}")
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
