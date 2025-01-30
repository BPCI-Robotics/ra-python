from vex import *

brain = Brain()
controller = Controller()

lift_intake = Motor(Ports.PORT7, GearSetting.RATIO_6_1, True)

BLUE_SIG = Signature(1, -4645, -3641, -4143,4431, 9695, 7063,2.5, 0)
RED_SIG = Signature(2, 7935, 9719, 8827,-1261, -289, -775,2.5, 0)

vision_sensor = Vision(Ports.PORT9, 50, BLUE_SIG, RED_SIG)

stake_grab_left = DigitalOut(brain.three_wire_port.a)
stake_grab_right = DigitalOut(brain.three_wire_port.b)

motor3 = Motor(Ports.PORT3, GearSetting.RATIO_6_1, False)
motor6 = Motor(Ports.PORT6, GearSetting.RATIO_6_1, True)

motor3.set_stopping(COAST)
motor6.set_stopping(COAST)

drivetrain= DriveTrain(
                MotorGroup(
                    Motor(Ports.PORT1, GearSetting.RATIO_6_1, False), 
                    Motor(Ports.PORT2, GearSetting.RATIO_6_1, False),
                    Motor(Ports.PORT3, GearSetting.RATIO_6_1, True),
                ), 
                    
                MotorGroup(
                    Motor(Ports.PORT4, GearSetting.RATIO_6_1, True), 
                    Motor(Ports.PORT5, GearSetting.RATIO_6_1, True), 
                    Motor(Ports.PORT6, GearSetting.RATIO_6_1, False),
                ), 
                
                259.34, # wheel travel
                310,    # track width
                205,     # wheel base
                MM,     # unit
                600/360 
            )

MY_SIG = BLUE_SIG

ENEMY_SIG = RED_SIG if MY_SIG == BLUE_SIG else BLUE_SIG

def set_stake(state: bool) -> None:
    stake_grab_left.set(state)
    stake_grab_right.set(state)

"""
def elevator_loop() -> None:
    while True:
        sleep(1000 / 30, MSEC)

        objects = vision_sensor.take_snapshot(MY_SIG)
        if objects and len(objects) > 0:
            continue

        positive = 0
        negative = 0
        for _ in range(50):
            objects = vision_sensor.take_snapshot(ENEMY_SIG)
            if objects and len(objects) > 0:
                positive += 1
            else:
                negative += 1
        
        objects = vision_sensor.largest_object().width
        brain.screen.set_cursor(1, 1)
        brain.screen.print(objects[0].height)
        if positive >= negative and objects[0].height > 40:
            sleep(400, MSEC)

            save_direction = lift_intake.direction()
            save_velocity = lift_intake.velocity()

            lift_intake.stop()
            sleep(200, MSEC)

            lift_intake.spin(save_direction, save_velocity, PERCENT)
"""

def _init() -> None:

    drivetrain.set_drive_velocity(0, PERCENT)
    drivetrain.set_turn_velocity(0, PERCENT)
    
    lift_intake.set_velocity(0, PERCENT)
    drivetrain.drive(FORWARD)

    drivetrain.set_stopping(COAST)
    lift_intake.set_stopping(BRAKE)

measurements = [0.0] * 30
measurements_index = 0

grabbing_stake = False
def toggle_stake():
    global grabbing_stake
    grabbing_stake = not grabbing_stake
    set_stake(grabbing_stake)


def _controls() -> None:
    
    controller.buttonL2.pressed(lift_intake.spin, (FORWARD, 100, PERCENT))
    controller.buttonL2.released(lift_intake.spin, (FORWARD, 0, PERCENT))
    controller.buttonL1.pressed(lift_intake.spin, (REVERSE, 100, PERCENT))
    controller.buttonL1.released(lift_intake.spin, (REVERSE, 0, PERCENT))

    lift_intake.spin(FORWARD, 100, PERCENT)

    controller.buttonA.pressed(toggle_stake)

def driver():
    lift_intake.stop()
    _init()
    lift_intake.stop()
    _controls()
    lift_intake.stop()
    # Thread(elevator_loop) # 30 ups
    lift_intake.stop()

    drivetrain.drive(FORWARD)
    while True:

        accel_stick = controller.axis3.position()
        turn_stick = controller.axis1.position()

        drivetrain.lm.set_velocity(accel_stick - turn_stick, PERCENT)
        drivetrain.rm.set_velocity(accel_stick + turn_stick, PERCENT)
        drivetrain.drive(FORWARD)

def auton():
    pass
    

competition = Competition(driver, auton)