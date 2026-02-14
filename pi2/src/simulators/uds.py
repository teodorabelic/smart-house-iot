import math
import random
import time

def run_uds_simulator(interval_sec, callback, stop_event, code):
    while not stop_event.is_set():
        cm = 80 + 40 * math.sin(time.time() / 5)
        callback(cm, code)
        time.sleep(interval_sec)
