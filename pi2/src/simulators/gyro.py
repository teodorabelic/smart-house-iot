import random


class GyroscopeSimulator:
    def read(self):
        return {'x': round(random.uniform(-20, 20), 2), 'y': round(random.uniform(-20, 20), 2), 'z': round(random.uniform(-20, 20), 2)}
