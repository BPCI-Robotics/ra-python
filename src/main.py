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

def set_stake(state: bool) -> None:
    stake_grab_left.set(state)
    stake_grab_right.set(state)

class ControlledMotor:
    def __init__(self, get: Callable[..., float], set: Callable[[float], Any], accel: float, brake: float, rate = 60):
        self.vel = 0.0
        self.setpoint = 0.0

        self.get = get
        self.set = set

        self.accel = accel
        self.brake = brake
        self.rate = rate

        self.running = False
    
    def start(self) -> None:
        self.running = True
        Thread(self._loop)
    
    def get_velocity(self) -> float:
        return self.vel
    
    def __call__(self, v: float):
        self.set_velocity(v)

    def set_velocity(self, v: float):
        if not self.running:
            self.start()
        self.setpoint = v

    def _loop(self):

        accel = self.accel
        brake = self.brake

        rate = self.rate

        while self.running:
            self.set(self.vel)

            # TODO: Check if this line should be removed.
            self.vel = self.get()

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
    
    def stop(self):
        self.running = False


def elevator_loop() -> None:
    while True:
        sleep(1000 / 30, MSEC)
        
        if (vision_sensor.object_count == 0):
            continue

        if (vision_sensor.take_snapshot(MY_SIG)):
            continue

        if (vision_sensor.take_snapshot(ENEMY_SIG) and lift_intake.is_spinning()):

            # TODO: Adjust this value!
            wait(400, MSEC)
            save_direction = lift_intake.direction()
            save_speed = lift_intake.velocity(PERCENT)

            lift_intake.stop()
            wait(300, MSEC)
            lift_intake.spin(save_direction, save_speed, PERCENT)
            

def debug_loop() -> None:
    while True:
        brain.screen.set_cursor(1, 1)
        brain.screen.print("LM:", drivetrain.lm.velocity())
        brain.screen.set_cursor(2, 1)
        brain.screen.print("RM:", drivetrain.rm.velocity())
        brain.screen.set_cursor(3, 1)
        brain.screen.print("Donut elevator:", lift_intake.direction(), lift_intake.is_spinning(), lift_intake.velocity())

        wait(100, MSEC)

def _init() -> None:
    global set_turn_velocity, set_drive_velocity

    def _get_turn_velocity() -> float:
        return (drivetrain.lm.velocity(PERCENT) - drivetrain.rm.velocity(PERCENT)) / 2

    def _set_turn_velocity(v: float):
        drivetrain.set_turn_velocity(v, PERCENT)

    def _get_drive_velocity() -> float:
        return drivetrain.velocity(PERCENT)

    def _set_drive_velocity(v: float):
        drivetrain.set_drive_velocity(v)

    # TODO: adjust the accel and brake parameters for optimal performance.
    set_turn_velocity = ControlledMotor(_get_turn_velocity, _set_turn_velocity, 100, 100, 60)
    set_drive_velocity = ControlledMotor(_get_drive_velocity, _set_drive_velocity, 100, 100, 60)

    drivetrain.set_drive_velocity(0, PERCENT)
    drivetrain.set_turn_velocity(0, PERCENT)
    
    drivetrain.drive(FORWARD)

    drivetrain.set_stopping(COAST)
    lift_intake.set_stopping(BRAKE)

def _controls() -> None:
    controller.axis1.changed(set_drive_velocity, (controller.axis1.position(),))
    controller.axis3.changed(set_turn_velocity, (controller.axis3.position(),))
    
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

    set_turn_velocity.start()
    set_drive_velocity.start()

    # Give power to the controller after PID is ready.
    _controls()

    Thread(elevator_loop) # 30 ups
    Thread(debug_loop)    # 10 ups

def auton():
    pass
    

competition = Competition(driver, auton)