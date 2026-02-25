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
from components.ds1 import run_ds1
from components.dpir1 import run_dpir1
from components.dms import run_dms
from components.dus1 import run_dus1
from components.webc import run_webc
from components.cli import run_cli
from actuators.led import Led
from actuators.buzzer import Buzzer
from components.actuator_listener import ActuatorController


def main():
    settings = load_settings('settings.json')
    pi_cfg = settings['pi']
    pi_id = pi_cfg['pi_id']
    device_name = pi_cfg['device_name']

    mqtt_cfg = settings['mqtt']
    base_topic = mqtt_cfg.get('base_topic', 'smarthome')
    qos = int(mqtt_cfg.get('qos', 1))

    mqtt = MqttClient(mqtt_cfg['host'], int(mqtt_cfg['port']), client_id=f'{pi_id}-{device_name}')
    mqtt.connect()

    batch_cfg = settings.get('batch', {})
    batch_sender = BatchSender(
        mqtt_client=mqtt,
        qos=qos,
        max_batch_size=int(batch_cfg.get('max_batch_size', 20)),
        flush_interval_sec=float(batch_cfg.get('flush_interval_sec', 2.0))
    )
    batch_sender.start()

    stop_event = threading.Event()
    threads = []

    if 'DS1' in settings:
        run_ds1(settings['DS1'], threads, stop_event, batch_sender, pi_id, device_name)
    if 'DPIR1' in settings:
        run_dpir1(settings['DPIR1'], threads, stop_event, batch_sender, pi_id, device_name)
    if 'DMS' in settings:
        run_dms(settings['DMS'], threads, stop_event, batch_sender, pi_id, device_name)
    if 'DUS1' in settings:
        run_dus1(settings['DUS1'], threads, stop_event, batch_sender, pi_id, device_name)
    if 'WEBC' in settings:
        run_webc(settings['WEBC'], threads, stop_event, batch_sender, pi_id, device_name)

    #LED
    led = None
    if 'DL' in comps and not comps['DL'].get('simulated', True):
        led = Led(comps['DL']['pin'])
        led.setup()

    #BUZEER
    buzzer = None
    if 'DB' in comps and not comps['DB'].get('simulated', True):
        buzzer = Buzzer(comps['DB']['pin'])
        buzzer.setup()

    controller = ActuatorController(settings, pi_id=pi_id, base_topic=base_topic, mqtt=mqtt, qos=qos, led=led, buzzer=buzzer)
    mqtt.subscribe_json(f'{base_topic}/{pi_id}/actuators/+/set', controller.handle, qos=qos)

    try:
        run_cli(controller, stop_event)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        stop_event.set()
        batch_sender.stop()
        for t in threads:
            t.join(timeout=1.0)
        batch_sender.join(timeout=2.0)
        mqtt.close()
        if GPIO is not None:
            GPIO.cleanup()


if __name__ == '__main__':
    main()
