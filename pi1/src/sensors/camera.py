import os
import subprocess
import time
from pathlib import Path
from threading import Lock

try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

try:
    import cv2
except Exception:
    cv2 = None


class CameraSensor:
    def __init__(self, resolution=(640, 480), storage_path='/tmp/camera_captures/'):
        self.resolution = tuple(resolution)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self.camera = None
        self.backend = None

    def initialize(self):
        with self.lock:
            if Picamera2 is not None:
                self.camera = Picamera2()
                config = self.camera.create_still_configuration(main={'size': self.resolution})
                self.camera.configure(config)
                self.camera.start()
                self.backend = 'picamera2'
                return
            if cv2 is not None:
                self.camera = cv2.VideoCapture(0)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                if self.camera.isOpened():
                    self.backend = 'opencv'
                    return
                self.camera.release()
                self.camera = None

            # Fallback koji radi na Raspberry Pi OS-u kada picamera2 modul nije instaliran.
            try:
                result = subprocess.run(
                    ['libcamera-still', '--version'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                )
                if result.returncode == 0:
                    self.backend = 'libcamera-still'
                    return
            except Exception:
                pass

            raise RuntimeError('Camera backend not available (picamera2/opencv/libcamera-still).')

    def capture_frame(self):
        with self.lock:
            ts = time.strftime('%Y%m%d_%H%M%S')
            ms = int((time.time() % 1) * 1000)
            filename = f'capture_{ts}_{ms:03d}.jpg'
            out = self.storage_path / filename
            if self.backend == 'picamera2':
                self.camera.capture_file(str(out))
            elif self.backend == 'opencv':
                ok, frame = self.camera.read()
                if not ok:
                    raise RuntimeError('Failed to read frame from OpenCV camera')
                cv2.imwrite(str(out), frame)
            elif self.backend == 'libcamera-still':
                cmd = [
                    'libcamera-still',
                    '-n',
                    '--immediate',
                    '--width',
                    str(self.resolution[0]),
                    '--height',
                    str(self.resolution[1]),
                    '-o',
                    str(out),
                ]
                result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=12)
                if result.returncode != 0:
                    err = result.stderr.decode('utf-8', errors='ignore').strip()
                    raise RuntimeError(f'libcamera-still failed: {err}')
            else:
                raise RuntimeError('Camera not initialized')
            return {
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'resolution': [self.resolution[0], self.resolution[1]],
                'filename': str(out),
                'backend': self.backend,
            }

    def cleanup(self):
        with self.lock:
            if self.backend == 'picamera2' and self.camera is not None:
                self.camera.stop()
            if self.backend == 'opencv' and self.camera is not None:
                self.camera.release()
