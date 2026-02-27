import shlex
import socket
import subprocess
import threading
import time
from datetime import datetime

from sensors.camera import CameraSensor
from simulators.camera import CameraSimulator


def _detect_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except Exception:
        return "127.0.0.1"


def _stop_process(proc):
    if proc is None:
        return
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
        proc.wait(timeout=2)


def run_webc(settings, threads, stop_event, batch_sender, pi_id, device_name):
    simulated = settings.get('simulated', True)
    interval = float(settings.get('capture_interval', 30))
    mode = str(settings.get('mode', 'snapshot')).strip().lower()
    resolution = settings.get('resolution', [640, 480])
    storage_path = settings.get('storage_path', '/tmp/camera_captures/')
    restart_on_error_sec = float(settings.get('restart_on_error_sec', 2.0))

    if not simulated and mode == 'mjpg_streamer':
        command = settings.get(
            'stream_command',
            'mjpg_streamer -i "input_uvc.so" -o "output_http.so -p 8080 -w /usr/local/share/mjpg-streamer/www"'
        )
        port = int(settings.get('stream_port', 8080))
        stream_path = str(settings.get('stream_path', '/?action=stream'))
        host = str(settings.get('stream_host', '')).strip() or _detect_local_ip()
        stream_url = f'http://{host}:{port}{stream_path}'
        cmd = shlex.split(command)
        proc = None

        def _start():
            nonlocal proc
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            time.sleep(0.8)
            if proc.poll() is not None:
                err = (proc.stderr.read() or b'').decode('utf-8', errors='ignore').strip()
                raise RuntimeError(err or 'mjpg_streamer failed to start')

        def _loop():
            nonlocal proc
            while not stop_event.is_set():
                try:
                    if proc is None or proc.poll() is not None:
                        if proc is not None and proc.poll() is not None:
                            print(f"[WEBC] mjpg_streamer stopped (code={proc.returncode}). Restarting...")
                        _start()
                        print(f"[WEBC] mjpg_streamer started: {stream_url}")

                    payload = {
                        '_topic': f'smarthome/{pi_id}/camera/WEBC/data',
                        'pi_id': pi_id,
                        'device_name': device_name,
                        'component': 'WEBC',
                        'value': {
                            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                            'backend': 'mjpg_streamer',
                            'stream_url': stream_url,
                            'running': proc.poll() is None,
                        },
                        'simulated': False,
                        'ts': datetime.utcnow().isoformat()
                    }
                    batch_sender.enqueue(payload)
                    stop_event.wait(interval)
                except Exception as exc:
                    print(f"[WEBC] Stream error: {exc}")
                    _stop_process(proc)
                    proc = None
                    stop_event.wait(restart_on_error_sec)
            _stop_process(proc)

        th = threading.Thread(target=_loop, daemon=True)
        th.start()
        threads.append(th)
        return

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
