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
                
                259.34, # wheel travel
                310,    # track width
                205,     # wheel base
                MM,     # unit
                600/360 # gear ratio (drivetrain rpm) / (motor rpm)
            )

MY_SIG = BLUE_SIG

ENEMY_SIG = RED_SIG if MY_SIG == BLUE_SIG else BLUE_SIG

def set_stake(state: bool) -> None:
    stake_grab_left.set(state)
    stake_grab_right.set(state)

def elevator_loop() -> None:
    while True:
        sleep(1000 / 30, MSEC)

        vision_sensor.take_snapshot(MY_SIG)


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



class RollingAverage:
    def __init__(self, getter, setter, size, poll_frequency):
        self.inputs = [0] * size
        self.pos = 0
        self.size = size
        self.poll_frequency = poll_frequency
        self.getter = getter
        self.setter = setter

        Thread(self.loop)
    
    def _add_element(self, n: float):
        self.inputs[self.pos] = n
        self.pos = (self.pos + 1) % self.size
    
    def _get_val(self):
        return sum(self.inputs) / self.size

    def loop(self):
        while True:
            wait(1 / self.poll_frequency, SECONDS)
            self._add_element(self.getter())
            self.setter(self._get_val(), PERCENT)


def _init() -> None:

    drivetrain.set_drive_velocity(0, PERCENT)
    drivetrain.set_turn_velocity(0, PERCENT)
    
    lift_intake.set_velocity(0, PERCENT)
    drivetrain.drive(FORWARD)

    drivetrain.set_stopping(COAST)
    lift_intake.set_stopping(BRAKE)

def _controls() -> None:

    RollingAverage(controller.axis1.position, drivetrain.set_drive_velocity, 30, 60)

    controller.axis3.changed(drivetrain.set_turn_velocity, (controller.axis3.position(),PERCENT))
    
    controller.buttonL2.pressed(lift_intake.spin, (FORWARD, 100, PERCENT))
    controller.buttonL2.released(lift_intake.spin, (FORWARD, 0, PERCENT))
    controller.buttonL1.pressed(lift_intake.spin, (REVERSE, 100, PERCENT))
    controller.buttonL1.released(lift_intake.spin, (REVERSE, 0, PERCENT))

    lift_intake.spin(FORWARD, 100, PERCENT)

    GRABBING = True

    controller.buttonR1.pressed(set_stake, (GRABBING,))
    controller.buttonR2.pressed(set_stake, (not GRABBING,))

def driver():
    global set_turn_velocity, set_drive_velocity
    _init()

    # Give power to the controller after PID is ready.
    _controls()

    Thread(elevator_loop) # 30 ups

def auton():
    pass
    

competition = Competition(driver, auton)
