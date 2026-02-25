import threading
from datetime import datetime
from sensors.dht import DHT11Sensor
from simulators.dht import DHT11Simulator


def run_dht_component(code, settings, threads, stop_event, batch_sender, pi_id, device_name, on_value=None):
    simulated = settings.get('simulate', False)
    sensor = DHT11Simulator() if simulated else DHT11Sensor(settings['pin'])
    interval = settings.get('read_interval', 5)

    def loop():
        while not stop_event.is_set():
            data = sensor.read()
            if on_value is not None:
                on_value(code, data)
            batch_sender.enqueue({
                '_topic': f'smarthome/{pi_id}/sensors/{code}',
                'pi_id': pi_id,
                'device_name': device_name,
                'code': code,
                'value': data,
                'simulated': simulated,
                'ts': datetime.utcnow().isoformat(),
            })
            stop_event.wait(interval)

    th = threading.Thread(target=loop, daemon=True)
    th.start(); threads.append(th)
