from components.dht_common import run_dht_component

def run_dht1(settings, threads, stop_event, batch_sender, pi_id, device_name):
    run_dht_component('DHT1', settings, threads, stop_event, batch_sender, pi_id, device_name)
