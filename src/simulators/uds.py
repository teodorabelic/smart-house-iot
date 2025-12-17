import random
import time

def run_uds_simulator(interval_sec, callback, stop_event, code):
    while not stop_event.is_set():
        cm = round(random.uniform(10.0, 150.0), 2)
        callback(cm, code)
        time.sleep(interval_sec)
