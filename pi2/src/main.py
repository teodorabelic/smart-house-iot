import threading

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except Exception:
    GPIO = None

from settings import load_settings
from mqtt.client import MqttClient
from mqtt.batch_sender import BatchSender
from components.ds2 import run_ds2
from components.dus2 import run_dus2
from components.dpir2 import run_dpir2
from components.seg7_display import run_seg7_display
from components.btn import run_btn
from components.dht3 import run_dht3
from components.gyro import run_gyro


def main():
    settings = load_settings('settings.json')
    device = settings['device']
    pi_id = device['name'].upper()
    device_name = device.get('location', pi_id)
    mqtt_cfg = settings['mqtt']
    qos = 1
    mqtt = MqttClient(mqtt_cfg.get('host', mqtt_cfg.get('broker', 'localhost')), int(mqtt_cfg['port']), client_id=f"{pi_id}-client")
    mqtt.connect()
    batch_sender = BatchSender(mqtt, qos=qos, max_batch_size=int(settings['batch_sender']['max_batch_size']), flush_interval_sec=float(settings['batch_sender']['interval']))
    batch_sender.start()

    stop_event = threading.Event(); threads = []
    comps = settings['components']
    run_ds2(comps['DS2'], threads, stop_event, batch_sender, pi_id, device_name)
    run_dus2(comps['DUS2'], threads, stop_event, batch_sender, pi_id, device_name)
    run_dpir2(comps['DPIR2'], threads, stop_event, batch_sender, pi_id, device_name)
    timer = run_seg7_display(comps['4SD'], threads, stop_event, batch_sender, pi_id, device_name)
    run_btn(comps['BTN'], threads, stop_event, batch_sender, pi_id, device_name)
    run_dht3(comps['DHT3'], threads, stop_event, batch_sender, pi_id, device_name)
    run_gyro(comps['GSG'], threads, stop_event, batch_sender, pi_id, device_name)

    def on_actuator(topic, payload):
        code = topic.split('/')[-2].upper()
        action = str(payload.get('action', '')).lower()
        if code == '4SD':
            if action == 'set':
                timer.seconds = max(0, int(payload.get('seconds', 0)))
                timer.blinking = False
            elif action == 'add':
                timer.add_seconds(int(payload.get('seconds', comps['4SD'].get('button_add_seconds', 30))))
            elif action == 'stop_blink':
                timer.blinking = False
        elif code == 'BTN':
            if action == 'add':
                timer.add_seconds(int(payload.get('seconds', comps['4SD'].get('button_add_seconds', 30))))

    mqtt.subscribe_json(f"smarthome/{pi_id}/actuators/+/set", on_actuator, qos=qos)

    print('PI2 running. Commands: add [n], exit')
    try:
        while not stop_event.is_set():
            cmd = input('PI2> ').strip().lower()
            if cmd == 'exit':
                break
            if cmd.startswith('add'):
                parts = cmd.split()
                timer.add_seconds(int(parts[1]) if len(parts) > 1 else None)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        stop_event.set(); batch_sender.stop()
        for t in threads: t.join(timeout=1)
        batch_sender.join(timeout=2); mqtt.close()
        if GPIO is not None: GPIO.cleanup()


if __name__ == '__main__':
    main()
