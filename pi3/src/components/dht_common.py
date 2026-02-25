import threading
from datetime import datetime
from simulators.dht import DHT11Simulator

def run_dht_component(code, settings, threads, stop_event, batch_sender, pi_id, device_name, on_value=None):
    simulated = settings.get('simulated', True)
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
                print(f"[{pi_id}] {code} value={data} simulated={simulated}")
                if on_value is not None:
                    on_value(code, data)
                
                if data['temperature'] is not None:
                    batch_sender.enqueue({
                        '_topic': f'smarthome/{pi_id}/sensors/{code}',
                        'pi_id': pi_id,
                        'device_name': device_name,
                        'code': code,
                        'value': data,
                        'simulated': simulated,
                        'ts': datetime.utcnow().isoformat(),
                    })
            except Exception as e:
                print(f"Greška na {code} ({pi_id}): {e}")
            
            if stop_event.wait(interval):
                break

        if hasattr(sensor, 'cleanup'):
            sensor.cleanup()

    th = threading.Thread(target=loop, daemon=True)
    th.start()
    threads.append(th)