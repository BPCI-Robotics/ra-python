from vex import *

brain = Brain()
controller = Controller()

lift_intake = Motor(Ports.PORT7, GearSetting.RATIO_6_1, False)

BLUE_SIG = Signature(1, -4645, -3641, -4143,4431, 9695, 7063,2.5, 0)
RED_SIG = Signature(2, 7935, 9719, 8827,-1261, -289, -775,2.5, 0)

vision_sensor = Vision(Ports.PORT9, 50, BLUE_SIG, RED_SIG)

stake_grab_left = DigitalOut(brain.three_wire_port.a)
stake_grab_right = DigitalOut(brain.three_wire_port.b)

drivetrain= DriveTrain(
                MotorGroup(
                    Motor(Ports.PORT1, GearSetting.RATIO_6_1, False), 
                    Motor(Ports.PORT2, GearSetting.RATIO_6_1, True), 
                    Motor(Ports.PORT3, GearSetting.RATIO_6_1, False)
                ), 
                    
                MotorGroup(
                    Motor(Ports.PORT4, GearSetting.RATIO_6_1, True), 
                    Motor(Ports.PORT5, GearSetting.RATIO_6_1, False), 
                    Motor(Ports.PORT6, GearSetting.RATIO_6_1, True)
                ), 
                
                319.19, # wheel travel
                295,    # track width
                40,     # wheel base
                MM,     # unit
                360/600 # gear ratio (drivetrain rpm) / (motor rpm)
            )

MY_SIG = BLUE_SIG

ENEMY_SIG = RED_SIG if MY_SIG == BLUE_SIG else BLUE_SIG

def set_stake(state):
    stake_grab_left.set(state)
    stake_grab_right.set(state)

class PID_Motor:
    def __init__(self, P: float, I: float, D: float, getter: Callable[[], float], setter: Callable[[float], None]):
        self.Kp = P
        self.Ki = I
        self.Kd = D

        self.get_val = getter
        self.set_val = setter

        self.setpoint = 0

    def __call__(self, setpoint):
        self.setpoint = setpoint
    
    def start(self):
        Thread(self.loop)
    
    def loop(self):
        # Value of offset - when the error is equal zero
        offset = 320
        
        time_prev = brain.timer.time(SECONDS)
        e_prev = 0

        Kp = self.Kp
        Ki = self.Ki
        Kd = self.Kd

        I = 0

        while True:
            sleep(1000 / 30, MSEC)

            time = brain.timer.time(SECONDS)

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

            self.set_val(MV)

def get_turn_velocity() -> float:
    return (drivetrain.lm.velocity() - drivetrain.rm.velocity()) / 2

def elevator_loop():
    while True:
        sleep(1000 / 30, MSEC)
        
        if (vision_sensor.object_count == 0):
            continue

        if (vision_sensor.take_snapshot(MY_SIG)):
            continue

        if (vision_sensor.take_snapshot(ENEMY_SIG)):
            save_state = lift_intake.is_spinning()
            save_direction = lift_intake.direction()
            save_speed = lift_intake.velocity(PERCENT)

            lift_intake.stop()
            wait(400, MSEC)
            
            if (save_state != lift_intake.is_spinning() or save_direction != lift_intake.direction()):
                continue

            if (save_state):
                lift_intake.spin(save_direction, save_speed, PERCENT)

def debug_loop():
    while True:
        brain.screen.set_cursor(1, 1)
        brain.screen.print("LM:", drivetrain.lm.velocity())
        brain.screen.set_cursor(2, 1)
        brain.screen.print("RM:", drivetrain.rm.velocity())
        brain.screen.set_cursor(3, 1)
        brain.screen.print("Donut elevator:", lift_intake.direction(), lift_intake.is_spinning(), lift_intake.velocity())

        wait(100, MSEC)

set_turn_velocity_PID = PID_Motor(0.6, 0.2, 0.1, get_turn_velocity, drivetrain.set_turn_velocity)
set_drive_velocity_PID = PID_Motor(0.6, 0.2, 0.1, drivetrain.velocity, drivetrain.set_drive_velocity)

def _init():
    drivetrain.set_drive_velocity(0, PERCENT)
    drivetrain.set_turn_velocity(0, PERCENT)
    
    drivetrain.drive(FORWARD)

    drivetrain.set_stopping(COAST)
    lift_intake.set_stopping(BRAKE)

def _controls():
    controller.axis1.changed(set_drive_velocity_PID, (controller.axis1.position(),))
    controller.axis3.changed(set_turn_velocity_PID, (controller.axis3.position(),))
    
    controller.buttonL2.pressed(lift_intake.spin, (FORWARD, 100, PERCENT))
    controller.buttonL2.released(lift_intake.spin, (FORWARD, 0, PERCENT))
    controller.buttonL1.pressed(lift_intake.spin, (REVERSE, 100, PERCENT))
    controller.buttonL1.released(lift_intake.spin, (REVERSE, 0, PERCENT))

    lift_intake.spin(FORWARD, 100, PERCENT)

    GRABBING = True

    controller.buttonR1.pressed(set_stake, (GRABBING,))
    controller.buttonR2.pressed(set_stake, (not GRABBING,))

def driver():

    _init()
    _controls()

    set_turn_velocity_PID.start()
    set_drive_velocity_PID.start()

    Thread(elevator_loop) # 30 ups
    Thread(debug_loop)    # 10 ups

competition = Competition(driver, lambda: None)