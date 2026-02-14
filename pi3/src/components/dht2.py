from components.dht_common import run_dht_component

def run_dht2(settings, threads, stop_event, batch_sender, pi_id, device_name):
    run_dht_component('DHT2', settings, threads, stop_event, batch_sender, pi_id, device_name)
