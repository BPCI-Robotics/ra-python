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
        Motor(Ports.PORT2, GearSetting.RATIO_6_1, True),
        Motor(Ports.PORT3, GearSetting.RATIO_6_1, False),
    )

rm= MotorGroup(
        Motor(Ports.PORT4, GearSetting.RATIO_6_1, True), 
        Motor(Ports.PORT5, GearSetting.RATIO_6_1, False), 
        Motor(Ports.PORT6, GearSetting.RATIO_6_1, True),
    )

vision_sensor = Vision(Ports.PORT9, 50, BLUE_SIG, RED_SIG)

stake_grabber = DigitalOut(brain.three_wire_port.a)
doink_piston = DigitalOut(brain.three_wire_port.b)
donut_detector = DigitalOut(brain.three_wire_port.c)

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

#which retard did this
#you can use // for floor in python you h*ckin dumb bunny
def floor(x: float) -> int:
    r = round(x)
    if r > x:
        return r - 1
    else:
        return r

class Option:
    def __init__(self, name: str, color: Color, choices: list[Any]):
        self.name = name
        self.color = color
        self.choices = choices
        self.index = 0
        self.length = len(choices)

    def value(self) -> Any:
        return self.choices[self.index]
    
    def next(self) -> None:
        self.index = (self.index + 1) % self.length

class SelectionMenu:
    def add_option(self, name: str, color: Color, choices: list[Any]):
        self.options.append(Option(name, color, choices))
        self.count += 1
    
    def __init__(self):
        self.count = 0
        self.options: list[Option] = []

        brain.screen.pressed(self.on_brain_screen_press)
    
    def on_brain_screen_press(self):
        x = brain.screen.x_position()
        y = brain.screen.y_position()

        if y < 240 - 30:
            return
        
        self.options[floor(x / self.count)].next()

        self.draw()
    
    def get_all(self):
        d = {}
        for option in self.options:
            d[option.name] = option.value()
        
        return d

    def draw(self):
        brain.screen.clear_screen(Color.BLACK)

        # Print the configurations
        brain.screen.set_font(FontType.MONO15)

        for i, option in enumerate(self.options):
            brain.screen.set_pen_color(option.color)
            brain.screen.set_cursor(i + 1, 1)
            brain.screen.print(option.name + ": " + option.value())
        
        # Draw the buttons
        # |--10--|Button|--10--|Button|--10--|Button|--10--|

        canvas_width = 480
        canvas_height = 240

        rect_width = (canvas_width - 10 * (self.count + 1)) / self.count
        rect_height = 30

        for i, option in enumerate(self.options):
            brain.screen.draw_rectangle(
                10 + (10 + rect_width) * i, 
                canvas_height - (rect_height + 5),
                rect_width,
                rect_height,
                option.color
            )  

class RollingAverage:
    def __init__(self, size: int):
        self.size = size
        self.data = [0.0] * self.size
        self.pos = 0
    
    def __call__(self, val: float) -> float:
        self.data[self.pos] = val
        self.pos = (self.pos + 1) % self.size

        return sum(self.data) / self.size

class WallStake:
    def __init__(self):
        self.motor = Motor(Ports.PORT8, GearSetting.RATIO_36_1, True)
        self.absolute0Position = self.motor.position(DEGREES)

    #any of the following functions may be changed to self.motor.spin_for(FORWARD, 70, DEGREES, 60, RPM)
    def pickup(self):
        self.motor.spin_to_position(70, DEGREES, 60, RPM)
            
    def hold(self):
        self.motor.spin_to_position(140, DEGREES, 60, RPM)
        
    def score(self):
        self.motor.spin_to_position(300, DEGREES, 70, RPM)

    def reset(self):
        self.motor.spin_to_position(self.absolute0Position, DEGREES, 70, RPM)

class LiftIntake:
    def __init__(self, enemy_sig):
        self.motor = Motor(Ports.PORT7, GearSetting.RATIO_36_1, False)
        self.running = False
        self.sorting_enabled = True
        self.enemy_sig = enemy_sig

        self.motor.set_stopping(BRAKE)
        Thread(self.sorting_loop)
    
    def spin(self, direction: DirectionType.DirectionType):
        self.running = True
        self.motor.spin(direction, 100, PERCENT)
    
    def stop(self):
        self.running = False
        self.motor.stop()

    def sorting_loop(self):

        while True:
            sleep(20, MSEC)

            # Exit: the lift intake isn't running or the user doesn't want to color sort.
            if not self.running or not self.sorting_enabled:
                continue

            enemy_donut = vision_sensor.take_snapshot(self.enemy_sig, 1)[0]


            # Exit: the donut is too far away (so it appears small)
            if enemy_donut.height < 30 or enemy_donut.width < 70:
                continue

            # Hold on, I found something. Let's wait until the switch is hit.
            timer = 0
            akita_neru = False

            while not donut_sensor.get_new_press():
                delay(10)
                timer += 10

                # 1. Two seconds have passed and the donut did not make it to the top.
                # 2. The lift intake is not spinning anymore. No need to continue waiting.
                # 3. The driver has asked to disable color sorting. No need to continue waiting.
                akita_neru = timer > 2000 or not lift_intake_running or not color_sort_enabled

                if akita_neru:
                    break

            # Exit: the donut did not make it to the top.
            if (akita_neru)
                continue

            save_direction = lift_intake.get_direction()

            delay(100)
            lift_intake.spin_for(REVERSE, 200, DEGREES)
            delay(250)

            lift_intake.move_velocity(600 * (save_direction == FORWARD ? 1 : -1))





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
    
    lift_intake.stop()
    drivetrain.drive(FORWARD)

    drivetrain.set_stopping(COAST)

    controller.buttonL2.pressed(lift_intake.spin, (FORWARD,))
    controller.buttonL2.released(lift_intake.stop)
    controller.buttonL1.pressed(lift_intake.spin, (REVERSE,))
    controller.buttonL1.released(lift_intake.stop)
    controller.buttonX.pressed(wall_stake.pickup)
    controller.buttonY.pressed(wall_stake.hold)
    controller.buttonA.pressed(wall_stake.score)
    controller.buttonB.pressed(wall_stake.reset)
    controller.buttonR2.pressed(toggle_stake)
    controller.buttonR1.pressed(toggle_doink_piston)

lift_intake = LiftIntake(RED_SIG)
wall_stake = WallStake()

def do_drive_loop() -> None:
    accel_stick = controller.axis3.position()
    turn_stick = controller.axis1.position()

    lm.spin(FORWARD, accel_stick - turn_stick, PERCENT)
    rm.spin(FORWARD, accel_stick + turn_stick, PERCENT)


def driver():
    init()
    while True:
        do_elevator_loop()
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
    wait(0.5, SECONDS)

    wall_stake.score()
    drivetrain.drive_for(REVERSE, 20, INCHES, 80, PERCENT)

    
        
    """release_stake()

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
"""
