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
    pi_cfg = settings['pi']
    pi_id = pi_cfg['pi_id']
    device_name = pi_cfg['device_name']
    mqtt_cfg = settings['mqtt']
    qos = int(mqtt_cfg.get('qos', 1))
    mqtt = MqttClient(mqtt_cfg.get('host', '127.0.0.1'), int(mqtt_cfg['port']), client_id=f'{pi_id}-client')
    mqtt.connect()
    batch_cfg = settings.get('batch', {})
    batch_sender = BatchSender(mqtt, qos=qos, max_batch_size=int(batch_cfg.get('max_batch_size', 50)), flush_interval_sec=float(batch_cfg.get('flush_interval_sec', 10)))
    batch_sender.start()

    stop_event = threading.Event(); threads = []
    comps = settings['components']

    latest = {'DHT1': None, 'DHT2': None, 'DHT3': None}

    def on_dht_value(code, value):
        latest[code] = value

    run_dht1(comps['DHT1'], threads, stop_event, batch_sender, pi_id, device_name, on_dht_value)
    run_dht2(comps['DHT2'], threads, stop_event, batch_sender, pi_id, device_name, on_dht_value)
    run_dpir3(comps['DPIR3'], threads, stop_event, batch_sender, pi_id, device_name)

    rgb = RGBController(comps['BRGB'], batch_sender, pi_id, device_name)
    run_ir_receiver(comps['IR'], threads, stop_event, batch_sender, pi_id, device_name, rgb.apply_command)

    def on_actuator(topic, payload):
        code = topic.split('/')[-2].upper()
        if code == 'BRGB':
            cmd = payload.get('action') or payload.get('command') or 'OFF'
            rgb.apply_command(cmd)

    mqtt.subscribe_json(f"smarthome/{pi_id}/actuators/+/set", on_actuator, qos=qos)

    order = ['DHT1', 'DHT2', 'DHT3']
    idx = {'i': 0}

    def lines():
        key = order[idx['i'] % len(order)]
        idx['i'] += 1
        v = latest.get(key) or {'temperature': '--', 'humidity': '--'}
        return (f'{key} T:{v["temperature"]}', f'H:{v["humidity"]}%')

    run_lcd_display(comps['LCD'], threads, stop_event, lines)

    print('PI3 running. Commands: rgb red|green|blue|off, exit')
    try:
        while not stop_event.is_set():
            cmd = input('PI3> ').strip().upper()
            if cmd == 'EXIT':
                break
            if cmd.startswith('RGB '):
                rgb.apply_command(cmd.split()[1])
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        stop_event.set(); batch_sender.stop()
        for t in threads: t.join(timeout=1)
        batch_sender.join(timeout=2); mqtt.close()
        if GPIO is not None: GPIO.cleanup()


if __name__ == '__main__':
    main()
