from vex import *

# region parts declaration
brain = Brain()
controller = Controller()

lift_intake = Motor(Ports.PORT7, GearSetting.RATIO_6_1, True)

BLUE_SIG = Signature(1, -4645, -3641, -4143,4431, 9695, 7063,2.5, 0)
RED_SIG = Signature(2, 7935, 9719, 8827,-1261, -289, -775,2.5, 0)

vision_sensor = Vision(Ports.PORT9, 50, BLUE_SIG, RED_SIG)

stake_grab_left = DigitalOut(brain.three_wire_port.a)
stake_grab_right = DigitalOut(brain.three_wire_port.b)

lm= MotorGroup(
        Motor(Ports.PORT1, GearSetting.RATIO_6_1, False), 
        Motor(Ports.PORT2, GearSetting.RATIO_6_1, False),
        Motor(Ports.PORT3, GearSetting.RATIO_6_1, True),
    )

rm= MotorGroup(
        Motor(Ports.PORT4, GearSetting.RATIO_6_1, True), 
        Motor(Ports.PORT5, GearSetting.RATIO_6_1, True), 
        Motor(Ports.PORT6, GearSetting.RATIO_6_1, False),
    )

drivetrain= DriveTrain(
                lm,
                rm,
                259.34, # wheel travel
                310,    # track width
                205,     # wheel base
                MM,     # unit
                600/360 
            )
# endregion

# CONFIG AREA 
MY_SIG = BLUE_SIG
# END CONFIG AREA

ENEMY_SIG = RED_SIG if MY_SIG == BLUE_SIG else BLUE_SIG

class RollingAverage:
    def __init__(self):
        self.size = 30
        self.data = [0.0] * self.size
        self.pos = 0
    
    def __call__(self, val: float) -> float:
        self.data[self.pos] = val
        self.pos = (self.pos + 1) % self.size

        return sum(self.data) / self.size

grabbing_stake = False
def toggle_stake():
    global grabbing_stake
    grabbing_stake = not grabbing_stake
    stake_grab_left.set(grabbing_stake)
    stake_grab_right.set(grabbing_stake)

def init():
    drivetrain.set_drive_velocity(0, PERCENT)
    drivetrain.set_turn_velocity(0, PERCENT)
    
    lift_intake.set_velocity(0, PERCENT)
    drivetrain.drive(FORWARD)

    drivetrain.set_stopping(COAST)
    lift_intake.set_stopping(BRAKE)

    controller.buttonL2.pressed(lift_intake.spin, (FORWARD, 100, PERCENT))
    controller.buttonL2.released(lift_intake.spin, (FORWARD, 0, PERCENT))
    controller.buttonL1.pressed(lift_intake.spin, (REVERSE, 100, PERCENT))
    controller.buttonL1.released(lift_intake.spin, (REVERSE, 0, PERCENT))

    controller.buttonA.pressed(toggle_stake)

def do_elevator_loop() -> None:
    
    my_objects = vision_sensor.take_snapshot(MY_SIG)
    enemy_objects = vision_sensor.take_snapshot(ENEMY_SIG)

    exists = lambda a: a and len(a) > 0

    if (exists(my_objects)):
        return

    if not exists(enemy_objects):
        return
    
    largest_object = vision_sensor.largest_object()

    if (largest_object.width > 100 or largest_object.height > 100) and lift_intake.velocity(PERCENT) > 0:

        wait(100, MSEC)

        save_direction = lift_intake.direction()
        save_speed = lift_intake.velocity(PERCENT)
        lift_intake.stop()

        wait(300, MSEC)

        lift_intake.spin(save_direction, save_speed, PERCENT)

control_accel = RollingAverage()
control_turn = RollingAverage()

def do_drive_loop() -> None:
    accel_stick = control_accel(controller.axis3.position())
    turn_stick = control_turn(controller.axis1.position())

    lm.set_velocity(accel_stick - turn_stick, PERCENT)
    rm.set_velocity(accel_stick + turn_stick, PERCENT)
    drivetrain.drive(FORWARD)


def driver():
    while True:
        do_elevator_loop()
        do_drive_loop()
        wait(1 / 60, SECONDS)

def auton():
    pass
    
competition = Competition(driver, auton)