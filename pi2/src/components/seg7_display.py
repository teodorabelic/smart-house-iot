import threading
import time
from datetime import datetime

try:
    import tm1637
except Exception:
    tm1637 = None


class Seg7Timer:
    def __init__(self, settings):
        self.seconds = int(settings.get('initial_seconds', 0))
        self.add_step = int(settings.get('button_add_seconds', 30))
        self.blinking = False
        self.simulate = settings.get('simulated', False)
        self._lock = threading.Lock()
        self.display = None
        if not self.simulate and tm1637 is not None:
            self.display = tm1637.TM1637(clk=settings['clk_pin'], dio=settings['dio_pin'])
            self.display.brightness(2)

    def add_seconds(self, value=None):
        with self._lock:
            self.seconds += int(value if value is not None else self.add_step)
            self.blinking = False

    def tick(self):
        with self._lock:
            if self.seconds > 0:
                self.seconds -= 1
            else:
                self.blinking = True
            return self.seconds, self.blinking

    def render(self, blink_on=True):
        with self._lock:
            mm = self.seconds // 60
            ss = self.seconds % 60
            if self.display is not None:
                if self.blinking and not blink_on:
                    self.display.show('    ')
                else:
                    self.display.numbers(mm, ss)
            return {'mm': mm, 'ss': ss, 'blinking': self.blinking}


def run_seg7_display(settings, threads, stop_event, batch_sender, pi_id, device_name):
    timer = Seg7Timer(settings)

    def loop():
        blink_on = True
        last_tick = time.time()
        while not stop_event.is_set():
            if time.time() - last_tick >= 1:
                timer.tick()
                last_tick = time.time()
            state = timer.render(blink_on)
            print(f"[{pi_id}] 4SD value={state} simulated={timer.simulate}")
            blink_on = not blink_on
            batch_sender.enqueue({
                '_topic': f'smarthome/{pi_id}/sensors/4SD',
                'pi_id': pi_id,
                'device_name': device_name,
                'code': '4SD',
                'value': state,
                'simulated': timer.simulate,
                'ts': datetime.utcnow().isoformat(),
            })
            stop_event.wait(0.5)

    th = threading.Thread(target=loop, daemon=True)
    th.start(); threads.append(th)
    return timer
