from vex import *

BLUE_SIG = Signature(1, -4645, -3641, -4143,4431, 9695, 7063,2.5, 0)
RED_SIG = Signature(2, 7935, 9719, 8827,-1261, -289, -775,2.5, 0)

# CONFIG AREA 
MY_SIG = BLUE_SIG
AUTON_STARTING_SIDE = RIGHT
# END CONFIG AREA

ENEMY_SIG = RED_SIG if MY_SIG == BLUE_SIG else BLUE_SIG

# region parts declaration
brain = Brain()
controller = Controller()

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

lift_intake = Motor(Ports.PORT7, GearSetting.RATIO_6_1, True)

vision_sensor = Vision(Ports.PORT9, 50, BLUE_SIG, RED_SIG)

stake_grabber = DigitalOut(brain.three_wire_port.a)
doink_piston = DigitalOut(brain.three_wire_port.b)

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

# https://www.cs2n.org/u/mp/badge_pages/2228
#
# (0, 0)                            (480, 0)
#
#
#
# (0, 240)                          (480, 240)

class Option:
    def __init__(self, name: str, color: Color, choices: list[Any]):
        self.name = name
        self.color = color
        self.choices = choices
        self.index = 0
        self.length = len(choices)

    def get(self) -> Any:
        return self.choices[self.index]
    
    def set(self) -> None:
        self.index = (self.index + 1) % self.length


class SelectionMenu:

    def add_option(self, name, color, default):
        self.options.append(Option(name, color, default))
        self.count += 1
    
    def __init__(self):
        self.count = 0
        self.options: list[Option] = []
    
    def draw(self):
        brain.screen.clear_screen(Color.BLACK)

        # Print the configurations
        brain.screen.set_font(FontType.MONO15)

        for i, option in enumerate(self.options):
            brain.screen.set_pen_color(option.color)
            brain.screen.set_cursor(i + 1, 1)
            brain.screen.print(option.name + ": " + option.get())
        
        # Draw the buttons
        # |--10--|Button|--10--|Button|--10--|Button|--10--|

        canvas_width = 480
        canvas_height = 240

        rect_width = (canvas_width - 10 * (self.count + 1)) / self.count
        rect_height = 20

        for i, option in enumerate(self.options):
            brain.screen.draw_rectangle(
                10 + (10 + rect_width) * i, 
                canvas_height - (rect_height + 5),
                rect_width,
                rect_height,
                option.color
            )

            

class RollingAverage:
    def __init__(self):
        self.size = 4
        self.data = [0.0] * self.size
        self.pos = 0
    
    def __call__(self, val: float) -> float:
        self.data[self.pos] = val
        self.pos = (self.pos + 1) % self.size

        return sum(self.data) / self.size

_stake_state = False
def toggle_stake():
    global _stake_state
    _stake_state = not _stake_state
    stake_grabber.set(_stake_state)
    
_doink_state = False
def toggle_doink_piston():
    global _doink_state
    _doink_state = not _doink_state
    doink_piston.set(_doink_state)

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
    controller.buttonR1.pressed(toggle_doink_piston)

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

    lm.spin(FORWARD, accel_stick - turn_stick, PERCENT)
    rm.spin(FORWARD, accel_stick + turn_stick, PERCENT)


def driver():
    init()
    while True:
        #do_elevator_loop()
        do_drive_loop()
        wait(1 / 60, SECONDS)


def release_stake():
    stake_grabber.set(False)

def grab_stake():
    stake_grabber.set(True)

def doinkDown():
    doink_piston.set(False)

def doinkUp():
    doink_piston.set(True)

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
