import random
import time

def run_binary_simulator(interval_sec, callback, stop_event, code, p_true=0.1):
    while not stop_event.is_set():
        value = (random.random() < p_true)
        callback(value, code)
        time.sleep(interval_sec)
