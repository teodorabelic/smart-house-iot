from components.ds_template import run_button_component

def run_ds2(settings, threads, stop_event, batch_sender, pi_id, device_name):
    run_button_component('DS2', settings, threads, stop_event, batch_sender, pi_id, device_name)
