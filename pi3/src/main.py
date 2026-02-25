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
from components.dht1 import run_dht1
from components.dht2 import run_dht2
from components.dpir3 import run_dpir3
from components.ir_receiver import run_ir_receiver
from components.rgb_led_ctrl import RGBController
from components.lcd_display import run_lcd_display

def main():
    settings = load_settings('settings.json')
    pi_id, device_name = settings['device']['id'], settings['device']['name']
    mqtt_cfg = settings['mqtt']
    
    mqtt = MqttClient(mqtt_cfg['host'], int(mqtt_cfg['port']), client_id=f"{pi_id}-client")
    mqtt.connect()

    batch_cfg = settings['batch']
    batch_sender = BatchSender(mqtt, qos=mqtt_cfg['qos'], max_batch_size=batch_cfg['max_batch_size'], flush_interval_sec=batch_cfg['flush_interval_sec'])
    batch_sender.start()

    stop_event = threading.Event()
    threads = []
    comps = settings['components']
    latest_dht = {'DHT1': None, 'DHT2': None, 'DHT3': None}

    def on_dht_value(code, value): latest_dht[code] = value

    run_dht1(comps['DHT1'], threads, stop_event, batch_sender, pi_id, device_name, on_dht_value)
    run_dht2(comps['DHT2'], threads, stop_event, batch_sender, pi_id, device_name, on_dht_value)
    run_dpir3(comps['DPIR3'], threads, stop_event, batch_sender, pi_id, device_name)

    # RGB Controller - On unutar sebe radi setup pinova
    rgb = RGBController(comps['BRGB'], batch_sender, pi_id, device_name)
    run_ir_receiver(comps['IR'], threads, stop_event, batch_sender, pi_id, device_name, rgb.apply_command)

    def publish_actuator_state(code, state):
        mqtt.publish_json(
            f"{mqtt_cfg['base_topic']}/{pi_id}/actuators/{code}/state",
            {"pi_id": pi_id, "code": code, "state": str(state)},
            qos=mqtt_cfg['qos'],
            retain=False,
        )

    def on_actuator(topic, payload):
        code = topic.split('/')[-2].upper()
        if code == 'BRGB':
            cmd = payload.get('action') or payload.get('command') or 'OFF'
            rgb.apply_command(cmd)
            publish_actuator_state('BRGB', str(cmd).upper())

    mqtt.subscribe_json(f"{mqtt_cfg['base_topic']}/{pi_id}/actuators/+/set", on_actuator)

    def on_remote_dht3(topic, payload):
        if payload.get('code') == 'DHT3' and isinstance(payload.get('value'), dict):
            latest_dht['DHT3'] = payload.get('value')

    mqtt.subscribe_json(f"{mqtt_cfg['base_topic']}/PI2/sensors/DHT3", on_remote_dht3)

    order = ['DHT1', 'DHT2', 'DHT3']; idx = [0]
    def get_lcd_lines():
        key = order[idx[0] % len(order)]; idx[0] += 1
        v = latest_dht.get(key) or {'temperature': '--', 'humidity': '--'}
        return (f"{key} T:{v['temperature']}", f"H:{v['humidity']}%")

    run_lcd_display(comps['LCD'], threads, stop_event, get_lcd_lines)

    try:
        while not stop_event.is_set():
            cmd = input(f"{pi_id}> ").strip().upper()
            if cmd == 'EXIT': break
            if cmd.startswith('RGB '): rgb.apply_command(cmd.split()[1])
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        stop_event.set()
        batch_sender.stop()
        for t in threads: t.join(timeout=1.0)
        mqtt.close()
        if GPIO: GPIO.cleanup()

if __name__ == '__main__':
    main()