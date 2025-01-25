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

stake_state = False

def toggle_stake():
    global stake_state
    stake_state = not stake_state

    stake_grab_left.set(stake_state)
    stake_grab_right.set(stake_state)

def elevator_loop():
    while True:
        sleep(20, MSEC)
        
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

        

def driver():
    drivetrain.set_drive_velocity(0, PERCENT)
    drivetrain.set_turn_velocity(0, PERCENT)
    drivetrain.set_stopping(COAST)
    drivetrain.drive(FORWARD)

    lift_intake.set_stopping(BRAKE)

    controller.axis1.changed(drivetrain.set_turn_velocity, (controller.axis1.position(), PERCENT))
    controller.axis3.changed(drivetrain.set_drive_velocity, (controller.axis3.position(), PERCENT))
    
    controller.buttonL2.pressed(lift_intake.spin, (FORWARD, 100, PERCENT))
    controller.buttonL2.released(lift_intake.spin, (FORWARD, 0, PERCENT))
    controller.buttonL1.pressed(lift_intake.spin, (REVERSE, 100, PERCENT))
    controller.buttonL1.released(lift_intake.spin, (REVERSE, 0, PERCENT))

    lift_intake.spin(FORWARD, 100, PERCENT)
    
    Thread(elevator_loop)
    Thread(debug_loop)

    controller.buttonR2.pressed(toggle_stake)

competition = Competition(driver, lambda: None)