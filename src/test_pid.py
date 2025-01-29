from vex_fake import *

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
CONFIG: dict[str, float] = {
    "Kp": 0.3,
    "Ki": 0.01,
    "Kd": 0.0,

    # When you crash, the integral term can crash out as the error accumulates. Setting this below one,
    # like 0.99 makes previous integral terms less valuable, preventing this issue. 
    "integral_decay": 0.9,
    
    # Acceleration and braking: measured in percent max speed per second. For example, a robot which
    # takes 0.5 seconds to reach max speed has 200 accel. If it takes 2 seconds to stop, it has 50 brake.
    # This isn't an adjustment, this is a simulation parameter. Make it match reality.
    "accel": 300,
    "brake": 300,

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
    set_velocity_pid(0)
    set_velocity_pid(100)
    sleep(2, SECONDS)
    set_velocity_pid(-100)
    sleep(4, SECONDS)
    set_velocity_pid(0)
    sleep(2, SECONDS)
    set_velocity_pid(100)
    sleep(0.6, SECONDS)
    set_velocity_pid(0)

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
        t = timer(SECONDS)

        if block:
            while abs(self.setpoint - self.get_val()) > 1:
                sleep(1 / 30, SECONDS)
    
    def start(self):
        self.running = True
        threading.Thread(target=self._loop).start()
    
    def stop(self):
        self.running = False

    def _loop(self):
        offset = 0
        
        time_prev = timer(SECONDS)
        e_prev = 0

        Kp = self.Kp
        Ki = self.Ki
        Kd = self.Kd

        I = 0

        while self.running:
            sleep(1 / 60, SECONDS)

            time = timer(SECONDS)

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



motor = Motor(200, 200)
set_velocity_pid = PID_Motor(CONFIG["Kp"], CONFIG["Ki"], CONFIG["Kd"], motor.get_velocity, motor.set_velocity)

crash = motor.crash

threading.Thread(target=ROUTINE).start()

while True:

    try: 
        if motor.vel > 200 or motor.vel < -200:
            set_velocity_pid.stop()
            motor.stop()
            exit(f"Value error. target: {motor.setpoint}, vel: {motor.vel}" )

        print(f"{round(motor.vel, 2)} -> {round(set_velocity_pid.setpoint, 2)} \t\t[" + "#" * abs(int((motor.vel/100)*40)) + " " * (40 - abs(int((motor.vel/100)*40))) + ("]" if motor.vel < 102 else ""))

        sleep(1 / CONFIG["poll_frequency"], SECONDS)
    
    except KeyboardInterrupt:
        break

set_velocity_pid.stop()
motor.stop()
exit("Stopped all threads.")