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

    # This is not thread-safe when block = True! It could deadlock!
    def __call__(self, setpoint: float, block = False):
        if (not self.running):
            self.start()
        
        self.setpoint = setpoint
        t = get_time()
        # print("Waiting for velocity to be", setpoint)

        if block:
            while abs(self.setpoint - self.get_val()) > 1:
                sleep(1 / 30)
        
        # print("Set velocity to", setpoint, "which took: ", round(get_time() - t, 2), "seconds.")
    
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
            sleep(1 / 60)

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
            # I *= 0.99

            self.set_val(self.get_val() + MV)

setpoint = 0
vel = 0

def _clamp(a, low, high):
    return max(min(a, high), low)

def get_velocity() -> float:
    global vel
    return vel

stop_loop = threading.Event()

def _set_velocity_loop():
    global vel, setpoint

    # Thes are measured in percent velocity / second. So max speed in 0.5 seconds is 200
    accel = 200
    brake = 10

    rate = 120

    while not stop_loop.is_set():
        sleep(1/rate)
        
        if vel < setpoint:
            if vel <= 0:
                vel += brake / rate
                continue

            if vel > 0:
                vel += accel / rate
                continue

        if vel > setpoint:
            if vel <= 0:
                vel -= accel / rate
                continue

            if vel > 0:
                vel -= brake / rate
                continue
            
threading.Thread(target=_set_velocity_loop).start()

def set_velocity(n: float):
    global setpoint
    setpoint = n

set_velocity_pid = PID_Motor(1, 0, 0, get_velocity, set_velocity)

target = 100

def _series():
    set_velocity_pid(100, True)
    sleep(1)
    set_velocity_pid(0, True)
    sleep(1)
    set_velocity_pid(75, True)
    sleep(1)
    set_velocity_pid(-86, True)
    sleep(1)
    set_velocity_pid(0, True)
    sleep(1)

threading.Thread(target=_series).start()

while True:

    try: 
        if vel > target * 2 or vel < - target * 2:
            set_velocity_pid.stop()
            stop_loop.set()
            exit(f"Value error. target: {target}, vel: {vel}" )

        print(f"{round(vel, 2)} -> {round(set_velocity_pid.setpoint, 2)} \t\t[" + "#" * abs(int((vel/target)*40)) + " " * (40 - abs(int((vel/target)*40))) + ("]" if vel < target + 1 else ""))
        sleep(1 / 15)
    
    except KeyboardInterrupt:
        break

set_velocity_pid.stop()
stop_loop.set()
exit("Stopped all threads.")