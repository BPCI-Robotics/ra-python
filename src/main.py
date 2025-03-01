from vex import *

# COMPLETED
class SelectionMenu:
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
    
    def __init__(self):
        self.count = 0
        self.options: list[SelectionMenu._Option] = []

        self.disabled = False
        self.enter_callback: Callable[[dict[str, Any]], None]

        brain.screen.pressed(self._on_brain_screen_press)

        self.add_option("Enter", Color.WHITE, ["", "Are you sure?", "ENTERED"])
    
    def on_enter(self, callback: Callable[[dict[str, Any]], None]):
        self.enter_callback = callback

    def add_option(self, name: str, color: Color | Color.DefinedColor, choices: list[Any]):
        if self.disabled:
            return
        
        self.options.insert(self.count - 1, SelectionMenu._Option(name, color, choices))
        self.count += 1
    
    def _on_brain_screen_press(self):
        if self.disabled:
            return
        
        x = brain.screen.x_position()
        y = brain.screen.y_position()

        if y < 240 - 100:
            return
        
        self.options[x * self.count // 480].next()

        self.draw()

        if self.options[self.count - 1].value() == "ENTERED":
            self.enter_callback(self._get_all())
            self.disabled = True
            return
    
    def force_submit(self):
            self.enter_callback(self._get_all())
            self.disabled = True
            return
    
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
            brain.screen.print(option.name + ": " + str(option.value()))

            i += 1

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

class WallStake:
    def __init__(self, motor: Motor, rotation: Rotation):
        self.motor = motor
        self.rotation = rotation

        self.motor.set_stopping(HOLD)
    
    def init(self):
        self.spin(REVERSE)
        wait(800, MSEC)
        self.rotation.reset_position()
        self.stop()

    def print_pos(self):
        while True:
            wait(200, MSEC)
            brain.screen.clear_screen()
            brain.screen.set_cursor(1, 1)
            brain.screen.print("Sensor:", self.rotation.position(DEGREES))
            brain.screen.set_cursor(2, 1)
            brain.screen.print("Motor:", self.motor.position(DEGREES))

    def start_log(self):
        Thread(self.print_pos)

    def pickup(self):
        self.motor.spin_to_position(25, DEGREES, 70, PERCENT)
            
    def spin(self, direction):
        self.motor.spin(direction, 70, PERCENT)

    def stop(self):
        self.motor.stop()
        
    def score(self):
        self.motor.spin_to_position(300, DEGREES, 60, PERCENT)

    def reset(self):
        self.motor.spin_to_position(0, DEGREES, 60, PERCENT)

# TODO: Clean up the starting and stopping of the loop.
# TODO: Debug why it doesn't reverse.

# Notes

# 4 possible places where color sort is failing (X means this reason is crossed out)
# 1: not detecting enemy signature properly (most likely)
# 2: logic for limit switch is off 
# 3: the loop isn't reset, as in once an enemy donut is detected
# 4: driver input might be interfering with it 

class LiftIntake:
    def __init__(self, motor: Motor, vision: Vision):
        self.motor = motor
        self.vision = vision

        self.sorting_enabled = False
        self.enemy_sig = None

        self.motor.set_stopping(BRAKE)
    
    def init(self):
        Thread(self._sorting_loop)
    
    def set_enemy_sig(self, enemy_sig):
        self.enemy_sig = enemy_sig

    def spin(self, direction: DirectionType.DirectionType):
        self.motor.spin(direction, 100, PERCENT)

    def stop(self):
        self.motor.stop()

    def _sorting_loop(self):

        while True:
            sleep(45, MSEC)

            enemy_donut = self.vision.take_snapshot(self.enemy_sig, 1)

            if not enemy_donut:
                continue

            # Exit: the donut is too far away (so it appears small)
            if enemy_donut[0].height < 50 or enemy_donut[0].width < 50:
                continue

            motor_position_initial = lift_intake.motor.position(DEGREES)

            while lift_intake.motor.position(DEGREES) < (motor_position_initial + 200):
                wait(20, MSEC)
            
            save_direction = self.motor.direction()
            
            wait(15, MSEC)
            self.stop()
            self.spin(REVERSE)
            wait(500, MSEC)

            self.spin(save_direction)

# COMPLETED
class DigitalOutToggleable(DigitalOut):
    def __init__(self, port, default_state=False):
        super().__init__(port)

        self.state = default_state

    def toggle(self):
        self.state = not self.state
        self.set(self.state)

class Auton:
    def __init__(self):
        self.direction = LEFT
        self._routine_selected = self._quals

    def _quals(self):
        if self.direction == LEFT:
            #run ring rush with alliance stake scoring

            drivetrain.drive_for(FORWARD, 25, INCHES, 80, PERCENT, True)
            drivetrain.turn_for(LEFT, 90, DEGREES, 75, PERCENT, True)
            drivetrain.drive_for(FORWARD, 2, INCHES, 60, PERCENT, True)
            #drivetrain.drive_for

            #give some time to stabilize
            wait(0.2, SECONDS)

            wall_stake.score()

            wait(1, SECONDS)

            drivetrain.drive_for(FORWARD, 5, INCHES, 90, PERCENT, True)
            drivetrain.drive_for(FORWARD, 5, INCHES, 90, PERCENT)
            wall_stake.reset()

            drivetrain.turn_for(LEFT, 55, DEGREES, 80, PERCENT)

            drivetrain.drive_for(REVERSE, 55, INCHES, 90, PERCENT)
            drivetrain.drive_for(FORWARD, 5, INCHES, 80, PERCENT)
            stake_grabber.toggle()

            wait(0.2, SECONDS)

            drivetrain.turn_for(RIGHT, 120, DEGREES, 85, PERCENT)

            lift_intake.spin(FORWARD)

            drivetrain.drive_for(FORWARD, 34, INCHES, 90, PERCENT)
            drivetrain.drive_for(REVERSE, 5, INCHES, 80, PERCENT)
            #after testing, we can add the above two lines again to pick up a third donut onto the stake

            drivetrain.turn_for(RIGHT, 90, DEGREES, 80, PERCENT)

            drivetrain.drive_for(FORWARD, 30, INCHES, 90, PERCENT)
            drivetrain.drive_for(REVERSE, 5, INCHES, 80, PERCENT)

            #check the time - if we don't have much time left, then just hit ladder
            drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT)
            drivetrain.drive_for(FORWARD, 60, INCHES, 90, PERCENT)

            #check the time - if we have time left, then the following code will apply

            #drivetrain.turn_for(LEFT, 90, DEGREES, 75, PERCENT)

            #drivetrain.drive_for(FORWARD, 51, INCHES, 90, PERCENT)
            
            #doink_piston.toggle()
            #drivetrain.drive_for(FORWARD, 10, INCHES, 80, PERCENT)
            #drivetrain.turn_for(LEFT, 70, DEGREES, 90, PERCENT)

        elif self.direction == RIGHT:
            #ts for goal rush
            drivetrain.drive_for(REVERSE, 40, INCHES, 85, PERCENT)
            drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
            stake_grabber.toggle()

            wait(0.3, SECONDS)
            #score the preload
            lift_intake.motor.spin_for(REVERSE, 2, TURNS)
            lift_intake.motor.spin_for(REVERSE, 1, TURNS)
            drivetrain.turn_for(LEFT, 90, DEGREES, 80, PERCENT)

            lift_intake.spin(FORWARD)

            drivetrain.drive_for(FORWARD, 35, INCHES, 90, PERCENT)
            wait(0.5, SECONDS)
            drivetrain.drive_for(REVERSE, 5, INCHES, 80, PERCENT)

            drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT)
            drivetrain.drive_for(FORWARD, 12, INCHES, 90, PERCENT)

            drivetrain.turn_for(LEFT, 90, DEGREES, 85, PERCENT)
            drivetrain.drive_for(FORWARD, 18, INCHES, 90, PERCENT)

            drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT)

            drivetrain.drive_for(FORWARD, 60, INCHES, 90, PERCENT)
            
            #clear corner
            doink_piston.toggle()
            drivetrain.drive_for(FORWARD, 10, INCHES, 80, PERCENT)
            drivetrain.turn_for(RIGHT, 116.6, DEGREES, 90, PERCENT)

    def _elims(self):
        if self.direction == LEFT:
            #its ring rush time
            #without alliance stake
            drivetrain.drive_for(REVERSE, 40, INCHES, 85, PERCENT)
            drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
            stake_grabber.toggle()

            wait(0.3, SECONDS)
            #score the preload
            lift_intake.motor.spin_for(REVERSE, 2, TURNS)
            lift_intake.motor.spin_for(REVERSE, 1, TURNS)
            drivetrain.turn_for(RIGHT, 90, DEGREES, 80, PERCENT)

            lift_intake.spin(FORWARD)

            drivetrain.drive_for(FORWARD, 20, INCHES)
            drivetrain.drive_for(REVERSE, 4, INCHES)

            drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT)
            #"thrust" the donuts
            drivetrain.drive_for(FORWARD, 18, INCHES, 85, PERCENT)
            drivetrain.drive_for(REVERSE, 7, INCHES, 85, PERCENT)
            drivetrain.turn_for(LEFT, 90, DEGREES, 85, PERCENT)
            drivetrain.drive_for(FORWARD, 8, INCHES, 85, PERCENT)
            drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT)
            drivetrain.drive_for(FORWARD, 8, INCHES, 80, PERCENT)
            drivetrain.drive_for(REVERSE, 8, INCHES, 85, PERCENT)

            drivetrain.turn_for(LEFT, 90, DEGREES, 75, PERCENT)
            drivetrain.drive_for(FORWARD, 14, INCHES, 90, PERCENT)
            drivetrain.turn_for(LEFT, 90, DEGREES, 85, PERCENT)

            drivetrain.drive_for(FORWARD, 51, INCHES, 90, PERCENT)
            
            doink_piston.toggle()
            drivetrain.drive_for(FORWARD, 10, INCHES, 80, PERCENT)
            drivetrain.turn_for(LEFT, 116.6, DEGREES, 90, PERCENT)
            
        elif self.direction == RIGHT:
            #ts for goal rush again
            drivetrain.drive_for(REVERSE, 40, INCHES, 85, PERCENT)
            drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
            stake_grabber.toggle()

            wait(0.3, SECONDS)
            #score the preload
            lift_intake.motor.spin_for(REVERSE, 2, TURNS)
            lift_intake.motor.spin_for(REVERSE, 1, TURNS)
            drivetrain.turn_for(LEFT, 90, DEGREES, 80, PERCENT)

            lift_intake.spin(FORWARD)

            drivetrain.drive_for(FORWARD, 35, INCHES, 90, PERCENT)
            wait(0.5, SECONDS)
            drivetrain.drive_for(REVERSE, 5, INCHES, 80, PERCENT)

            drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT)
            drivetrain.drive_for(FORWARD, 12, INCHES, 90, PERCENT)

            drivetrain.turn_for(LEFT, 90, DEGREES, 85, PERCENT)
            drivetrain.drive_for(FORWARD, 18, INCHES, 90, PERCENT)

            drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT)

            drivetrain.drive_for(FORWARD, 60, INCHES, 90, PERCENT)
            
            #clear corner
            doink_piston.toggle()
            drivetrain.drive_for(FORWARD, 10, INCHES, 80, PERCENT)
            drivetrain.turn_for(RIGHT, 70, DEGREES, 90, PERCENT)

    def _skills(self):
        #routine plan

        pass
    
    def set_config(self, config: dict[str, Any]):
        print(config)

        if config["Team color"] == "Red":
            lift_intake.set_enemy_sig(BLUE_SIG)
        else:
            lift_intake.set_enemy_sig(RED_SIG)
        
        if config["Auton direction"] == "Left":
            self.direction = LEFT
        else:
            self.direction = RIGHT
        
        if config["Auton type"] == "Skills":
            self._routine_selected = self._skills

        elif config['Auton type'] == "Quals":
            self._routine_selected = self._quals

        elif config['Auton type'] == "Elims":
            self._routine_selected = self._elims

    def __call__(self):
        lift_intake.init()
        wall_stake.start_log()

        self._routine_selected()

#region Parts
BLUE_SIG = Signature(1, -4645, -3641, -4143,4431, 9695, 7063, 2.5, 0)
RED_SIG = Signature(2, 7935, 9719, 8827,-1261, -289, -775, 2.5, 0)

brain = Brain()
controller = Controller()

stake_grabber = DigitalOutToggleable(brain.three_wire_port.a)
doink_piston = DigitalOutToggleable(brain.three_wire_port.b)

drivetrain= SmartDrive(
                MotorGroup(
                    Motor(Ports.PORT1, GearSetting.RATIO_6_1, False), 
                    Motor(Ports.PORT2, GearSetting.RATIO_6_1, True),
                    Motor(Ports.PORT3, GearSetting.RATIO_6_1, False),
                ),

                MotorGroup(
                    Motor(Ports.PORT4, GearSetting.RATIO_6_1, True), 
                    Motor(Ports.PORT5, GearSetting.RATIO_6_1, False), 
                    Motor(Ports.PORT6, GearSetting.RATIO_6_1, True),
                ),

                Inertial(Ports.PORT10), 

                259.34, # wheel travel
                310,    # track width
                205,    # wheel base
                MM,     # unit
                600/360
            )

lift_intake = LiftIntake(
    Motor(Ports.PORT7, GearSetting.RATIO_6_1, True), 
    Vision(Ports.PORT9, 50, BLUE_SIG, RED_SIG), 
)

wall_stake = WallStake(Motor(Ports.PORT8, GearSetting.RATIO_36_1, False), Rotation(Ports.PORT11))

#endregion Parts

def initialize():
    menu = SelectionMenu()

    menu.add_option("Team color", Color.RED, ["Red", "Blue"])
    menu.add_option("Auton direction", Color.BLUE, ["Left", "Right"])
    menu.add_option("Auton type", Color.PURPLE, ["Quals", "Elims", "Skills"])
    menu.add_option("Testing", Color.CYAN, ["Driver Control", "Auton"])

    menu.on_enter(auton.set_config)
    
    menu.draw()
    print("\033[2J")
    controller.buttonLeft.pressed(menu.force_submit)

def driver():
    lift_intake.init()
    wall_stake.start_log()

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
    controller.buttonB.pressed(wall_stake.reset)

    controller.buttonY.pressed(wall_stake.start)
    controller.buttonY.released(wall_stake.stop)

    controller.buttonA.pressed(wall_stake.reverse)
    controller.buttonA.released(wall_stake.stop)

    controller.buttonR2.pressed(stake_grabber.toggle)
    controller.buttonR1.pressed(doink_piston.toggle)
    
    while True:
        accel_stick = controller.axis3.position()
        turn_stick = controller.axis1.position()

        drivetrain.lm.spin(FORWARD, accel_stick - turn_stick, PERCENT)
        drivetrain.rm.spin(FORWARD, accel_stick + turn_stick, PERCENT)

        wait(1 / 60, SECONDS)

auton = Auton()

Competition(driver, auton)
initialize()
