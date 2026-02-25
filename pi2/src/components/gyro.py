import threading
from datetime import datetime
from simulators.gyro import GyroscopeSimulator

def run_gyro(settings, threads, stop_event, batch_sender, pi_id, device_name):

    simulated = settings.get('simulated', True)
    interval = settings.get('interval', 1)
    threshold = float(settings.get('threshold', 10.0))

    if simulated:
        sensor = GyroscopeSimulator()
    else:
        # Importujemo hardversku klasu SAMO ako nam zaista treba
        from sensors.gyroscope import GyroscopeSensor
        sensor = GyroscopeSensor(settings.get('i2c_address', '0x68'))

    def loop():
        while not stop_event.is_set():
            try:
                data = sensor.read()
                magnitude = abs(data['x']) + abs(data['y']) + abs(data['z'])
                print(f"[{pi_id}] GSG value={data} significant={magnitude >= threshold} simulated={simulated}")
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
            except Exception as e:
                print(f"Greška na Žiroskopu ({pi_id}): {e}")

            if stop_event.wait(interval):
                break

    th = threading.Thread(target=loop, daemon=True)
    th.start()
    threads.append(th)