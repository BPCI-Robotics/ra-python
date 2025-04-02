from vex import *

wall_stake_motor = Motor(Ports.PORT8, GearSetting.RATIO_36_1, True)
rotation_sensor = Rotation(Ports.PORT9, True)
controller_1 = Controller(PRIMARY)
brain = Brain()

from vex import *

# Begin project code
class LiftIntake:
    def __init__(self, motor: Motor):
        self.motor = motor
        self.enemy_sig = None

        self.motor.set_stopping(BRAKE)
    
    def set_enemy_sig(self, enemy_sig):
        self.enemy_sig = enemy_sig

    def spin(self, direction: DirectionType.DirectionType):
        self.motor.spin(direction, 100, PERCENT)

    def stop(self):
        self.motor.stop()

class WallStake:
    def __init__(self, motor: Motor, rotation: Rotation):
        self.motor = motor
        self.rotation = rotation

        self.motor.set_stopping(HOLD)
        self.init()

    def spin_to(self, target, unit):
        time_spent = 0
        while abs(target - self.rotation.position(unit)) > 4 or time_spent > 1000:
            if target > self.rotation.position(unit):
                self.motor.spin(FORWARD, 60, PERCENT)
            
            if target < self.rotation.position(unit):
                self.motor.spin(REVERSE, 60, PERCENT)

            wait(20, MSEC)
            time_spent += 20
        
        self.motor.stop()
    
    def init(self):
        self.spin(REVERSE) 
        wait(800, MSEC)
        self.rotation.reset_position()
        self.motor.set_position(0, DEGREES)
        self.stop()

    def print_pos(self):
        while True:
            wait(200, MSEC)
            brain.screen.clear_screen()
            brain.screen.set_cursor(1, 1)
            brain.screen.print("Rotation position", self.rotation.position(DEGREES))
            brain.screen.set_cursor(2, 1)
            brain.screen.print("Motor position", self.motor.position(DEGREES))

    def start_log(self):
        Thread(self.print_pos)

    def pickup(self):
        self.spin_to(36, DEGREES)

    def score(self):
        self.spin_to(192.48, DEGREES)

    def reset(self):
        self.spin_to(0, DEGREES)
            
    def spin(self, direction):
        self.motor.spin(direction, 30, PERCENT)

    def stop(self):
        self.motor.stop()

def main():
    wall_stake = WallStake(wall_stake_motor, rotation_sensor)
    wall_stake.start_log()
    lift_intake = LiftIntake(
        Motor(Ports.PORT7, GearSetting.RATIO_6_1, True),  
    )
    controller_1.buttonUp.pressed(wall_stake.spin, (FORWARD,))
    controller_1.buttonDown.pressed(wall_stake.spin, (REVERSE,))
    controller_1.buttonUp.released(wall_stake.stop)
    controller_1.buttonDown.released(wall_stake.stop)

    controller_1.buttonL2.pressed(lift_intake.spin, (FORWARD,))
    controller_1.buttonL2.released(lift_intake.stop)
    controller_1.buttonL1.pressed(lift_intake.spin, (REVERSE,))
    controller_1.buttonL1.released(lift_intake.stop)

main()
