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
    pi_id = settings['device']['name']
    mqtt_cfg = settings['mqtt']
    mqtt = MqttClient(mqtt_cfg['broker'], int(mqtt_cfg['port']), client_id=f'{pi_id}-client')
    mqtt.connect()
    batch_sender = BatchSender(mqtt, qos=1, max_batch_size=int(settings['batch_sender']['max_batch_size']), flush_interval_sec=float(settings['batch_sender']['interval']))
    batch_sender.start()

    stop_event = threading.Event(); threads = []
    comps = settings['components']
    run_dht1(comps['DHT1'], threads, stop_event, batch_sender, pi_id, pi_id)
    run_dht2(comps['DHT2'], threads, stop_event, batch_sender, pi_id, pi_id)
    run_dpir3(comps['DPIR3'], threads, stop_event, batch_sender, pi_id, pi_id)

    rgb = RGBController(comps['BRGB'], batch_sender, pi_id, pi_id)
    run_ir_receiver(comps['IR'], threads, stop_event, batch_sender, pi_id, pi_id, rgb.apply_command)

    latest = {'DHT1': None, 'DHT2': None, 'DHT3': None}

    def lines():
        for key in ['DHT1', 'DHT2', 'DHT3']:
            v = latest.get(key) or {'temperature': '--', 'humidity': '--'}
            if v:
                return (f'{key} T:{v["temperature"]}', f'H:{v["humidity"]}%')
        return ('Smart House', 'No DHT data')

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
