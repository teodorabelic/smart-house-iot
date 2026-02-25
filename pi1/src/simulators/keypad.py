import random
import time

KEYS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "#", "A", "B", "C", "D"]


def run_keypad_simulator(interval_sec, callback, stop_event, code):
    while not stop_event.is_set():
        callback(random.choice(KEYS), code)
        time.sleep(interval_sec)
