import time
from typing import Callable
from types import SimpleNamespace as Namespace
import threading

type vexnumber = float
type time_units = float


MSEC = 0.001
SECONDS = 1
def sleep(t: vexnumber, u: time_units):
    time.sleep(t * u)

def Thread(fn: Callable[..., None]):
    threading.Thread(target=fn).start()

def timer(u: time_units):
    return time.time() * u

class Motor:
    def __init__(self, accel: float, brake: float):
        self.vel = 0.0
        self.setpoint = 0.0

        self.accel = accel
        self.brake = brake

        self.running = True
        Thread(self._loop)
    
    def get_velocity(self) -> float:
        return self.vel
    
    def set_velocity(self, v: float):
        self.setpoint = v

    def _loop(self):

        accel = self.accel
        brake = self.brake

        rate = 120

        while self.running:
            sleep(1/rate, SECONDS)
            
            if self.vel < self.setpoint:
                if self.vel <= 0:
                    self.vel += brake / rate
                    continue

                if self.vel > 0:
                    self.vel += accel / rate
                    continue

            if self.vel > self.setpoint:
                if self.vel <= 0:
                    self.vel -= accel / rate
                    continue

                if self.vel > 0:
                    self.vel -= brake / rate
                    continue

    def crash(self, v=0.0, t=0.0):
        time_start = timer(SECONDS)

        self.vel = v
        print("Crashed!")
        while (timer(SECONDS) - time_start < t):
            self.vel = v
    
    def stop(self):
        self.running = False
