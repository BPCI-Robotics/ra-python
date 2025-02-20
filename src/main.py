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
donut_detector = Limit(brain.three_wire_port.c)

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

class _Option:
    def __init__(self, name: str, color: Color | Color.DefinedColor, choices: list[Any]):
        self.name = name
        self.color = color
        self.choices = choices
        self.index = 0
        self.count = len(choices)

    def value(self) -> Any:
        return self.choices[self.index]
    
    def next(self) -> None:
        self.index = (self.index + 1) % self.count
    
    def prev(self) -> None:
        if self.index == 0:
            self.index = self.count - 1
        else:
            self.index -= 1

class SelectionMenu:
    
    def __init__(self):
        self.count = 0
        self.options: list[_Option] = []

        self.select = 0

        self.disabled = False
        self.enter_callbacks: list[Callable[[dict[str, Any]], None]] = []

        brain.screen.pressed(self._on_brain_screen_press)

        controller.buttonLeft.pressed(self._on_arrow_event, ('L',))
        controller.buttonRight.pressed(self._on_arrow_event, ('R',))
        controller.buttonUp.pressed(self._on_arrow_event, ('U',))
        controller.buttonDown.pressed(self._on_arrow_event, ('D',))

        self.add_option("Enter", Color.WHITE, ["", "Are you sure?", "ENTERED"])
    
    def on_enter(self, callback: Callable[[dict[str, Any]], None]):
        self.enter_callbacks.append(callback)

    def _on_arrow_event(self, event):
        if self.disabled:
            return
        
        if event == 'L':
            self.options[self.select].prev()
        
        if event == 'R':
            self.options[self.select].next()
        
        if event == 'U':
            if self.select == 0:
                self.select = self.count - 1
            else:
                self.select -= 1
          
        if event == 'D':
            self.select = (self.select + 1) % self.count
        
        if self.options[self.count - 1].value() == "ENTERED":
            for callback in self.enter_callbacks:
                callback(self._get_all())
            self.draw()
            self.disabled = True
            return
        
        if self.select != self.count - 1 and self.options[self.count - 1].index != 0:
            self.options[self.count - 1].index = 0

        self.draw()

    def add_option(self, name: str, color: Color | Color.DefinedColor, choices: list[Any]):
        if self.disabled:
            return
        
        self.options.insert(self.count - 1, _Option(name, color, choices))
        self.count += 1

        self.draw()
    
    def _on_brain_screen_press(self):
        if self.disabled:
            return
        
        x = brain.screen.x_position()
        y = brain.screen.y_position()

        if y < 240 - 100:
            return
        
        self.options[x * self.count // 480].next()

        self.draw()
    
    def _get_all(self) -> dict[str, Any]:
        if self.disabled:
            return {}
        
        d = {}
        for option in self.options:
            d[option.name] = option.value()
        
        return d

    def draw(self):
        if self.disabled:
            return
        
        brain.screen.clear_screen(Color.BLACK)

        # Print the configurations
        brain.screen.set_font(FontType.MONO20)

        i = 0
        for option in self.options:
            brain.screen.set_pen_color(option.color)
            brain.screen.set_cursor(i + 1, 1)
            select_marker = ">> " if self.select == i else "   "
            brain.screen.print(select_marker + option.name + ": " + str(option.value()))

            i += 1
        
        # Draw the buttons
        # |--10--|Button|--10--|Button|--10--|Button|--10--|

        canvas_width = 480
        canvas_height = 240

        rect_width = (canvas_width - 10 * (self.count + 1)) / self.count
        rect_height = 70

        i = 0
        for option in self.options:
            brain.screen.set_pen_color(option.color)
            brain.screen.draw_rectangle(
                10 + (10 + rect_width) * i, 
                canvas_height - (rect_height + 5),
                rect_width,
                rect_height,
                option.color
            )
            i += 1

class PIDMotor:
     def __init__(self, P: float, I: float, D: float, getter: Callable[[], float], setter: Callable[[float], None]):
        self.Kp = P
        self.Ki = I
        self.Kd = D

        self.get_val = getter
        self.set_val = setter

        self.setpoint = 0

        self.running = False

     def start(self):
        self.running = True  

     def __call__(self, setpoint: float, block = False):
        if (not self.running):
            self.start()
        
        self.setpoint = setpoint
        t = brain.timer.time(SECONDS)
        # print("Waiting for velocity to be", setpoint)
        if block:
            while abs(self.setpoint - self.get_val()) > 1:
                sleep(1 / 30, SECONDS)

     def loop(self):
        # Value of offset - when the error is equal zero
        offset = 0
        time_prev = brain.timer.time(SECONDS)
        e_prev = 0

        Kp = self.Kp
        Ki = self.Ki
        Kd = self.Kd
        I = 0

        while self.running:
            sleep(1 / 60, SECONDS)

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
            I *= 0.99


            self.set_val(self.get_val() + MV)


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


def released_callback():
    return 
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

    def spin_for(self, direction: DirectionType.DirectionType, rpm, encoder_units):
        self.running = True
        self.motor.spin_for(direction, rpm, encoder_units)
    
    def get_direction(self):
        return self.motor.direction()
    
    def move_velocity(self, speed):
        self.motor.set_velocity(speed)

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

            while  donut_detector.released(released_callback):
                wait(10)
                timer += 10

                # 1. Two seconds have passed and the donut did not make it to the top.
                # 2. The lift intake is not spinning anymore. No need to continue waiting.
                # 3. The driver has asked to disable color sorting. No need to continue waiting.
                akita_neru = timer > 2000 or not self.running or not self.sorting_enabled

                if akita_neru:
                    break

            # Exit: the donut did not make it to the top.
            if (akita_neru):
                continue

            save_direction = lift_intake.get_direction()

            wait(100)
            lift_intake.spin_for(REVERSE, 200, DEGREES)
            wait(250)

            lift_intake.move_velocity(600 * (1 if save_direction == REVERSE else -1))

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
        lift_intake.sorting_loop()
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
        lift_intake.sorting_loop()
        wait(1/60, SECONDS)

def auton():
    wait(0.5, SECONDS)

    wall_stake.score()
    drivetrain.drive_for(REVERSE, 20, INCHES, 80, PERCENT)

    drivetrain.turn_for(LEFT, 90, DEGREES, 85, wait=True)

    auton_elevator_loop()
    drivetrain.drive_for(FORWARD, 85, INCHES, 90, PERCENT)
    
    
    #idk i left out the rest of the auton
        
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


        
