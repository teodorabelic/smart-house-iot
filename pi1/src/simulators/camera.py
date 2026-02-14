import time
from pathlib import Path


class CameraSimulator:
    def __init__(self, resolution=(640, 480), storage_path='/tmp/camera_captures/'):
        self.resolution = tuple(resolution)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def initialize(self):
        return None

    def capture_frame(self):
        ts = time.strftime('%Y%m%d_%H%M%S')
        filename = self.storage_path / f'sim_capture_{ts}.jpg'
        filename.write_text('simulated frame', encoding='utf-8')
        return {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'resolution': [self.resolution[0], self.resolution[1]],
            'filename': str(filename)
        }

    def cleanup(self):
        return None
