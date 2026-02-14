import random


class DHT11Simulator:
    def read(self):
        return {'temperature': round(random.uniform(20, 28), 1), 'humidity': round(random.uniform(35, 70), 1)}
