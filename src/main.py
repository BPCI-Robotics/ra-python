from vex import *

# region parts declaration
brain = Brain()
controller = Controller()

lift_intake = Motor(Ports.PORT7, GearSetting.RATIO_6_1, True)

BLUE_SIG = Signature(1, -4645, -3641, -4143,4431, 9695, 7063,2.5, 0)
RED_SIG = Signature(2, 7935, 9719, 8827,-1261, -289, -775,2.5, 0)

vision_sensor = Vision(Ports.PORT9, 50, BLUE_SIG, RED_SIG)

stake_grab_piston = DigitalOut(brain.three_wire_port.a)
doink_piston = DigitalOut(brain.three_wire_port.b)


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
AUTON_STARTING_SIDE = RIGHT
# END CONFIG AREA

ENEMY_SIG = RED_SIG if MY_SIG == BLUE_SIG else BLUE_SIG

class RollingAverage:
    def __init__(self, size=8, anti_lag=False):
        self.size = size
        self.anti_lag_enabled = anti_lag

        self.data = [0.0] * self.size
        self.pos = 0

    
    def __call__(self, val: float) -> float:

        # Add to the buffer, with a dead zone from -5 to 5
        self.data[self.pos] = 0 if -5 <= val <= 5 else val

        # Iterate to the next position
        self.pos = (self.pos + 1) % self.size
        
        ret = sum(self.data) / self.size
        ret_sign = -1 if ret < 0 else 1
        
        # Anti lag makes any value above 40 equivalent to 100.
        if abs(ret) > 50 and self.anti_lag_enabled:
            return ret_sign * 100

        return ret

doinking = False
def toggle_stake():
    global doinking
    doinking = not doinking
    doink_piston.set(doinking)

doinking = False
def doink_doink():
    global grabbing_stake
    grabbing_stake = not grabbing_stake
    stake_grab_piston.set(grabbing_stake)

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

    controller.buttonR2.pressed(toggle_stake)
    controller.buttonR1.pressed(doink_doink)

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
        doink_it()

        wait(300, MSEC)

        lift_intake.spin(save_direction, save_speed, PERCENT)

control_accel = RollingAverage(size=8, anti_lag=True)
control_turn = RollingAverage(size=15, anti_lag=False)

def do_drive_loop() -> None:
    accel_stick = control_accel(controller.axis3.position())
    turn_stick = control_turn(controller.axis1.position())

    lm.spin(FORWARD, accel_stick - turn_stick, PERCENT)
    rm.spin(FORWARD, accel_stick + turn_stick, PERCENT)


def driver():
    init()
    while True:
        do_elevator_loop()
        do_drive_loop()
        wait(1 / 60, SECONDS)


def release_stake():
    stake_grab_piston.set(False)

def grab_stake():
    stake_grab_piston.set(True)

def auton_elevator_loop():
    while True:
        do_elevator_loop()
        wait(1/60, SECONDS)

def auton():
    release_stake()

    # Wait for the piston to finish retracting.
    wait(0.3, SECONDS)

    # Drive backwards into a stake
    drivetrain.drive_for(REVERSE, 32, INCHES, 65, PERCENT)

    # Wait for the robot to stabilize
    wait(0.5, SECONDS)

    # Grab the stake
    grab_stake()

    # Wait for the piston to finish extending.
    wait(0.2, SECONDS)

    # Turn to grab the stake.
    drivetrain.turn_for(AUTON_STARTING_SIDE, 45, DEGREES)

    # Realign the stake after turning.
    drivetrain.drive_for(FORWARD, 2, INCHES)

    # Start the color sorting routine (remove if problematic)
    Thread(auton_elevator_loop)

    # Start the donut elevator and intake.
    lift_intake.spin(FORWARD, 100, PERCENT)

    # Wait to score.
    wait(1, SECONDS)

    # Goes in a direction depending on AUTON_STARTING_SIDE, picks up a donut that way.
    drivetrain.drive_for(FORWARD, 26, INCHES, 40, PERCENT)

    # Wait to score.
    wait(2, SECONDS)

    # Done.
    drivetrain.stop()
    lift_intake.stop()
    
competition = Competition(driver, auton)