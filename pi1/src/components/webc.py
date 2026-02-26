import threading
import time
from datetime import datetime

from sensors.camera import CameraSensor
from simulators.camera import CameraSimulator


def run_webc(settings, threads, stop_event, batch_sender, pi_id, device_name):
    simulated = settings.get('simulated', True)
    interval = float(settings.get('capture_interval', 30))
    resolution = settings.get('resolution', [640, 480])
    storage_path = settings.get('storage_path', '/tmp/camera_captures/')
    restart_on_error_sec = float(settings.get('restart_on_error_sec', 2.0))

    camera = CameraSimulator(resolution, storage_path) if simulated else CameraSensor(resolution, storage_path)
    try:
        camera.initialize()
    except Exception as exc:
        print(f"[WEBC] Camera init failed ({exc}). Falling back to simulator.")
        simulated = True
        camera = CameraSimulator(resolution, storage_path)
        camera.initialize()

    def _loop():
        while not stop_event.is_set():
            try:
                data = camera.capture_frame()
                payload = {
                    '_topic': f'smarthome/{pi_id}/camera/WEBC/data',
                    'pi_id': pi_id,
                    'device_name': device_name,
                    'component': 'WEBC',
                    'value': data,
                    'simulated': simulated,
                    'ts': datetime.utcnow().isoformat()
                }
                print('[WEBC]', payload['value'])
                batch_sender.enqueue(payload)
                stop_event.wait(interval)
            except Exception as exc:
                print(f"[WEBC] Capture error: {exc}")
                stop_event.wait(restart_on_error_sec)
        try:
            camera.cleanup()
        except Exception:
            pass

    th = threading.Thread(target=_loop, daemon=True)
    th.start()
    threads.append(th)
