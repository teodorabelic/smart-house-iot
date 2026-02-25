from datetime import datetime
from actuators.rgb_led import RGBLed
from simulators.rgb import RGBSimulator


class RGBController:
    MAP = {
        'RED': (100, 0, 0),
        'GREEN': (0, 100, 0),
        'BLUE': (0, 0, 100),
        'OFF': (0, 0, 0),
        'POWER': (100, 100, 100),
        'WHITE': (100, 100, 100),
    }

    def __init__(self, settings, batch_sender, pi_id, device_name):
        self.simulate = settings.get('simulated', False)
        self.batch_sender = batch_sender
        self.pi_id = pi_id
        self.device_name = device_name
        self.driver = RGBSimulator() if self.simulate else RGBLed(settings['pins'], simulate=False)
        if hasattr(self.driver, 'initialize'):
            self.driver.initialize()

    def apply_command(self, cmd):
        cmd = str(cmd).upper()
        color = self.MAP.get(cmd, (0, 0, 0))
        state = self.driver.set_color(*color)
        print(f"[{self.pi_id}] BRGB command={cmd} color={state} simulated={self.simulate}")
        self.batch_sender.enqueue({
            '_topic': f'smarthome/{self.pi_id}/sensors/BRGB',
            'pi_id': self.pi_id,
            'device_name': self.device_name,
            'code': 'BRGB',
            'value': {'command': cmd, 'color': state},
            'simulated': self.simulate,
            'ts': datetime.utcnow().isoformat(),
        })
