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
from actuators.led import Led
from actuators.buzzer import Buzzer
from components.actuator_listener import ActuatorController

def main():
    settings = load_settings('settings.json')
    pi_id, device_name = settings['device']['id'], settings['device']['name']
    mqtt_cfg = settings['mqtt']
    
    mqtt = MqttClient(mqtt_cfg['host'], int(mqtt_cfg['port']), client_id=f"{pi_id}-{device_name}")
    mqtt.connect()

    batch_cfg = settings['batch']
    batch_sender = BatchSender(mqtt, qos=mqtt_cfg['qos'], 
                               max_batch_size=batch_cfg['max_batch_size'], 
                               flush_interval_sec=batch_cfg['flush_interval_sec'])
    batch_sender.start()

    stop_event = threading.Event()
    threads = []
    comps = settings['components']

    # Senzori
    if 'DS1' in comps: run_ds1(comps['DS1'], threads, stop_event, batch_sender, pi_id, device_name)
    if 'DPIR1' in comps: run_dpir1(comps['DPIR1'], threads, stop_event, batch_sender, pi_id, device_name)
    if 'DMS' in comps: run_dms(comps['DMS'], threads, stop_event, batch_sender, pi_id, device_name)
    if 'DUS1' in comps: run_dus1(comps['DUS1'], threads, stop_event, batch_sender, pi_id, device_name)
    if 'WEBC' in comps: run_webc(comps['WEBC'], threads, stop_event, batch_sender, pi_id, device_name)

    # Aktuatori
    led = None
    if 'DL' in comps:
        led = Led(comps['DL']['pin'])
        if not comps['DL'].get('simulated', True): led.setup()

    buzzer = None
    if 'DB' in comps:
        buzzer = Buzzer(comps['DB']['pin'])
        if not comps['DB'].get('simulated', True): buzzer.setup()

    controller = ActuatorController(settings, pi_id=pi_id, base_topic=mqtt_cfg['base_topic'], mqtt=mqtt, qos=mqtt_cfg['qos'], led=led, buzzer=buzzer)
    mqtt.subscribe_json(f"{mqtt_cfg['base_topic']}/{pi_id}/actuators/+/set", controller.handle)

    try:
        while not stop_event.is_set():
            cmd = input(f"{pi_id}> ").strip().lower()
            if cmd == 'exit': break
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