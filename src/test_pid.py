# This code runs on a computer.
from time import time as get_time
from time import sleep
from typing import Callable
import threading
from pprint import pprint


class PID_Motor:
    def __init__(self, P: float, I: float, D: float, getter: Callable[[], float], setter: Callable[[float], None]):
        self.Kp = P
        self.Ki = I
        self.Kd = D

        self.get_val = getter
        self.set_val = setter

        self.setpoint = 0

        self.running = False

    def __call__(self, setpoint: float):
        if (not self.running):
            self.start()
        self.setpoint = setpoint
    
    def start(self):
        self.running = True
        threading.Thread(target=self.loop).start()
    
    def stop(self):
        self.running = False

    def loop(self):
        # Value of offset - when the error is equal zero
        offset = 0
        
        time_prev = get_time()
        e_prev = 0

        Kp = self.Kp
        Ki = self.Ki
        Kd = self.Kd

        I = 0

        while self.running:
            sleep(1 / 30)

            time = get_time()

            # PID calculations
            e = self.setpoint - self.get_val()
                
            P = Kp*e
            I += Ki*e*(time - time_prev)
            D = Kd*(e - e_prev)/(time - time_prev)

            # calculate manipulated variable - MV 
            MV = offset + P + I + D

            # update stored data for next iteration
            e_prev = e
            time_prev = time
            I *= 0.99

            self.set_val(self.get_val() + MV * 0.1)

vel = 0

def _clamp(a, low, high):
    return max(min(a, high), low)

def get_velocity() -> float:
    global vel
    return vel

def set_velocity(n: float):
    global vel
    vel = n

set_velocity_pid = PID_Motor(0.1, 0, 0, get_velocity, set_velocity)
set_velocity_pid.start()

while True:
    target = 100

    set_velocity_pid(target)

    while (abs(vel - target) > 0.01):

        if vel > target * 2 or vel < 0:
            set_velocity_pid.stop()
            exit(f"Value error. target: {target}, vel: {vel}" )

        print(f"{round(vel, 2)} -> {round(target, 2)} \t\t[" + "#" * int((vel/target)*40) + " " * (40 - int((vel/target)*40)) + "]")
        sleep(1 / 10)