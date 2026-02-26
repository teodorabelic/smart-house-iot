import time
from pathlib import Path


class CameraSimulator:
    def __init__(self, resolution=(640, 480), storage_path='/tmp/camera_captures/'):
        self.resolution = tuple(resolution)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.frame_index = 0

    def initialize(self):
        return None

    @staticmethod
    def _write_bmp(path: Path, width: int, height: int, frame_index: int):
        width = max(64, int(width))
        height = max(64, int(height))

        row_padding = (4 - (width * 3) % 4) % 4
        row_size = width * 3 + row_padding
        pixel_data_size = row_size * height
        file_size = 14 + 40 + pixel_data_size

        header = bytearray()
        header.extend(b'BM')
        header.extend(file_size.to_bytes(4, 'little'))
        header.extend((0).to_bytes(2, 'little'))
        header.extend((0).to_bytes(2, 'little'))
        header.extend((54).to_bytes(4, 'little'))
        header.extend((40).to_bytes(4, 'little'))
        header.extend(width.to_bytes(4, 'little', signed=True))
        header.extend(height.to_bytes(4, 'little', signed=True))
        header.extend((1).to_bytes(2, 'little'))
        header.extend((24).to_bytes(2, 'little'))
        header.extend((0).to_bytes(4, 'little'))
        header.extend(pixel_data_size.to_bytes(4, 'little'))
        header.extend((2835).to_bytes(4, 'little'))
        header.extend((2835).to_bytes(4, 'little'))
        header.extend((0).to_bytes(4, 'little'))
        header.extend((0).to_bytes(4, 'little'))

        # 3 pokretne vertikalne trake + gradijent da bude očigledno da se frame menja.
        phase = frame_index % width
        stripe_w = max(8, width // 12)
        pad = b'\x00' * row_padding
        pixels = bytearray()
        for y in range(height - 1, -1, -1):
            yv = (y * 255) // max(1, height - 1)
            for x in range(width):
                in_r = phase <= x < min(width, phase + stripe_w)
                in_g = (phase * 2) % width <= x < min(width, ((phase * 2) % width) + stripe_w)
                in_b = (phase * 3) % width <= x < min(width, ((phase * 3) % width) + stripe_w)

                r = 255 if in_r else (x * 255) // max(1, width - 1)
                g = 255 if in_g else yv
                b = 255 if in_b else ((x + y + frame_index * 5) % 256)
                pixels.extend((b, g, r))
            pixels.extend(pad)

        path.write_bytes(bytes(header) + bytes(pixels))

    def capture_frame(self):
        ts = time.strftime('%Y%m%d_%H%M%S')
        ms = int((time.time() % 1) * 1000)
        filename = self.storage_path / f'sim_capture_{ts}_{ms:03d}.bmp'
        self._write_bmp(filename, self.resolution[0], self.resolution[1], self.frame_index)
        self.frame_index += 1
        return {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'resolution': [self.resolution[0], self.resolution[1]],
            'filename': str(filename),
            'backend': 'simulator',
        }

    def cleanup(self):
        return None
