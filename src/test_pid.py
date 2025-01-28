from time import time as get_time
from time import sleep
from typing import Callable
import threading

# Here is a bunch of parameters you might want to try.
#
# PID values: Be very careful with adjustments, small adjustments make a big difference. Keep it in
#             0.1s. If it is wrong, it can cause exponential growth and cause the program to fail.
#
# Proportional: if only this is set, it will linearly approach the target velocity.
#               This is the one that should be set first.
# Integral: this makes the robot more impatient when it is slow.
#           It builds up as the error remains high for a while. Use carefully.
# Derivative: this is based on how much the error changes over time.
#             If there is a lot of oscillation, try changing this.
CONFIG = {
    "Kp": 1,
    "Ki": 0,
    "Kd": 0,

    # When you crash, the integral term can crash out as the error accumulates. Setting this below one,
    # like 0.99 makes previous integral terms less valuable, preventing this issue. 
    "integral_decay": 1,
    
    # Acceleration and braking: measured in percent max speed per second. For example, a robot which
    # takes 0.5 seconds to reach max speed has 200 accel. If it takes 2 seconds to stop, it has 50 brake.
    # This isn't an adjustment, this is a simulation parameter. Make it match reality.
    "accel": 200,
    "brake": 200,

    # Frequency at which to print the current velocity.
    "poll_frequency": 15,
}

# set_velocity_pid: instruct pid to change the velocity, second parameter stops execution until velocity
#                   is reached. If it is not given, it doesn't wait.
#
# sleep: Sleep for a given number of seconds.
#
# crash: Directly set the actual velocity to a given number, 0 by default. This simulates an unexpected
#        change in velocity. It also has an additional time parameter, where it gets stuck for a certain
#        number of seconds. Test integral windup this way.
def ROUTINE():
    set_velocity_pid(100, True)
    sleep(1)
    set_velocity_pid(0, True)
    sleep(1)
    set_velocity_pid(75, False)
    sleep(0.4)
    crash(0, 2)
    sleep(1)
    set_velocity_pid(-86, True)
    sleep(1)
    set_velocity_pid(0, True)
    sleep(1)

# Everything past here is messy implementation and you probably don't want to touch it.

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
            I *= CONFIG["integral_decay"]

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
    accel = CONFIG["accel"]
    brake = CONFIG["brake"]

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

def crash(v=0.0, t=0.0):
    global vel
    time_start = get_time()

    vel = v
    print("Crashed!")
    while (get_time() - time_start < t):
        vel = v


def set_velocity(n: float):
    global setpoint
    setpoint = n

set_velocity_pid = PID_Motor(CONFIG["Kp"], CONFIG["Ki"], CONFIG["Kd"], get_velocity, set_velocity)

target = 100

threading.Thread(target=ROUTINE).start()

while True:

    try: 
        if vel > target * 2 or vel < - target * 2:
            set_velocity_pid.stop()
            stop_loop.set()
            exit(f"Value error. target: {target}, vel: {vel}" )

        print(f"{round(vel, 2)} -> {round(set_velocity_pid.setpoint, 2)} \t\t[" + "#" * abs(int((vel/target)*40)) + " " * (40 - abs(int((vel/target)*40))) + ("]" if vel < target + 1 else ""))
        sleep(1 / CONFIG["poll_frequency"])
    
    except KeyboardInterrupt:
        break

set_velocity_pid.stop()
stop_loop.set()
exit("Stopped all threads.")