import random


class IRSimulator:
    CODES = ['POWER', 'RED', 'GREEN', 'BLUE', 'OFF', 'NONE']
    def read(self):
        return random.choice(self.CODES)
