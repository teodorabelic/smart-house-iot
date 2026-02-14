from components.ds_template import run_button_component

def run_btn(settings, threads, stop_event, batch_sender, pi_id, device_name):
    run_button_component('BTN', settings, threads, stop_event, batch_sender, pi_id, device_name)
