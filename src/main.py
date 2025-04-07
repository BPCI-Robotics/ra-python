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

# COMPLETED
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
        self.rotation.reset_position()
        self.stop()

    def print_pos(self):
        while True:
            wait(200, MSEC)
            brain.screen.clear_screen()
            brain.screen.set_cursor(1, 1)
            brain.screen.print("Intake temp:", lift_intake.motor.temperature())
            brain.screen.set_cursor(2, 1)
            brain.screen.print("Wall stake temp:", wall_stake.motor.temperature())
            brain.screen.set_cursor(3, 1)
            brain.screen.print("Drivetrain temp:", drivetrain.temperature())

    def start_log(self):
        Thread(self.print_pos)

    def pickup(self):
        self.spin_to(23.5, DEGREES)

    def score(self):
        self.spin_to(192.48, DEGREES)

    def reset(self):
        self.spin_to(0, DEGREES)
            
    def spin(self, direction):
        self.motor.spin(direction, 60, PERCENT)

    def stop(self):
        self.motor.stop()

# COMPLETED
class LiftIntake:
    def __init__(self, motor: Motor):
        self.motor = motor
        self.enemy_sig = None

        self.motor.set_stopping(BRAKE)

    def spin(self, direction: DirectionType.DirectionType):
        self.motor.spin(direction, 100, PERCENT)

    def stop(self):
        self.motor.stop()

# COMPLETED
class DigitalOutToggleable(DigitalOut):
    def __init__(self, port, default_state=False):
        super().__init__(port)

        self.state = default_state

    def toggle(self):
        self.state = not self.state
        self.set(self.state)

RED_SIG = 0
BLUE_SIG = 1

class Auton:
    def __init__(self):
        self.direction = LEFT
        self._routine_selected = self._noop
        self.color = RED_SIG
        self.mode = "Ring"

        drivetrain.set_heading(0, DEGREES)
        drivetrain.set_rotation(0, DEGREES)
        drivetrain.set_turn_velocity(75, PERCENT)
        drivetrain.set_drive_velocity(60, PERCENT)

    def _noop(self):
        pass

    def _skills(self):
        while True:
            d.turn_to_heading(0, DEGREES)
            d.drive_for(12, INCHES)
            d.turn_to_heading(90, DEGREES)
            d.drive_for(12, INCHES)
            d.turn_to_heading(180, DEGREES)
            d.drive_for(12, INCHES)
            d.turn_to_heading(270, DEGREES)
            d.drive_for(12, INCHES)
            d.turn_to_heading(360, DEGREES)
        

    def _quals(self):
        pass

    def _elims(self):
        pass

    def set_config(self, config: dict[str, Any]):
        print(config)

        if config["Team color"] == "Red":
            self.color = RED_SIG
        else:
            self.color = BLUE_SIG
        
        if config["Auton direction"] == "Left":
            self.direction = LEFT
        else:
            self.direction = RIGHT

        if config["Ring/Goal rush"] == "Ring":
            self.mode = "Ring"
        
        else:
            self.mode = "Goal"
        
        if config["Auton type"] == "Skills":
            self._routine_selected = self._skills

        elif config['Auton type'] == "Quals":
            self._routine_selected = self._quals

        elif config['Auton type'] == "Elims":
            self._routine_selected = self._elims

    def __call__(self):
        wall_stake.start_log()
        self._routine_selected()

#region Parts
brain = Brain()
controller = Controller()

stake_grabber = DigitalOutToggleable(brain.three_wire_port.a)
doink_piston = DigitalOutToggleable(brain.three_wire_port.b)

inertial = Inertial(Ports.PORT10)

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

                inertial, 

                259.34, # wheel travel
                315,    # track width
                280,    # wheel base
                MM,     # unit
                600/360
            )
d = drivetrain

lift_intake = LiftIntake(Motor(Ports.PORT7, GearSetting.RATIO_6_1, True))

wall_stake = WallStake(Motor(Ports.PORT8, GearSetting.RATIO_36_1, True), Rotation(Ports.PORT9))

#endregion Parts

def initialize():
    inertial.calibrate()
    drivetrain.set_turn_constant(1)

    menu = SelectionMenu()

    menu.add_option("Team color", Color.RED, ["Red", "Blue"])
    menu.add_option("Auton direction", Color.BLUE, ["Left", "Right"])
    menu.add_option("Auton type", Color.PURPLE, ["Quals", "Elims", "Skills"])
    menu.add_option("Ring/Goal rush", Color.CYAN, ["Ring", "Goal"])

    menu.on_enter(auton.set_config)
    
    menu.draw()
    print("\033[2J")
    controller.buttonLeft.pressed(menu.force_submit)

def driver():
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

    controller.buttonY.pressed(wall_stake.spin, (REVERSE,))
    controller.buttonY.released(wall_stake.stop)

    controller.buttonA.pressed(wall_stake.spin, (FORWARD,))
    controller.buttonA.released(wall_stake.stop)

    controller.buttonR2.pressed(stake_grabber.toggle)
    controller.buttonR1.pressed(doink_piston.toggle)
    
    while True:
        accel_stick = controller.axis3.position()
        turn_stick = controller.axis1.position()

        drivetrain.lm.set_velocity(accel_stick - turn_stick, PERCENT)
        drivetrain.rm.set_velocity(accel_stick + turn_stick, PERCENT)

        wait(1 / 60, SECONDS)

auton = Auton()

Competition(driver, auton)
initialize()
