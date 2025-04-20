
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
        while abs(target - self.rotation.position(unit)) > 0 or time_spent > 1000:
            if target > self.rotation.position(unit):
                self.motor.spin(FORWARD, 60, PERCENT)
            
            if target < self.rotation.position(unit):
                self.motor.spin(REVERSE, 60, PERCENT)

            wait(20, MSEC)
            time_spent += 20
        
        self.motor.stop()
        

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
        if self.color == RED_SIG:
            #run ring rush with alliance stake scoring
            drivetrain.drive_for(FORWARD, 36, INCHES, 60, PERCENT, wait=True)
            drivetrain.drive_for(FORWARD, 2, INCHES, 60, PERCENT)
            #drivetrain.drive_for

            wait(0.8, SECONDS)

            wall_stake.spin_to(212, DEGREES)

            wait(1, SECONDS)

            wall_stake.spin_to(359, DEGREES)

            wait(0.5, SECONDS)

            drivetrain.drive_for(REVERSE, 68, INCHES, 90, PERCENT, True)
            stake_grabber.toggle()

            drivetrain.turn_to_heading(180, DEGREES)

            #drivetrain.turn_for(LEFT, 205, DEGREES, 90, PERCENT)

            drivetrain.drive_for(REVERSE, 55, INCHES, 90, PERCENT)
            drivetrain.drive_for(FORWARD, 5, INCHES, 80, PERCENT)

            wait(0.2, SECONDS)

            drivetrain.turn_for(RIGHT, 120, DEGREES, 85, PERCENT)

            """lift_intake.spin(FORWARD)

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
            #drivetrain.turn_for(LEFT, 70, DEGREES, 90, PERCENT)"""

        elif self.color == BLUE_SIG:
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
        drivetrain.set_timeout(5, SECONDS)
        if self.color == RED_SIG:
            if self.mode == "Ring":
                #its ring rush time
                #RED 
                #without alliance stake
                drivetrain.drive_for(REVERSE, 60, INCHES, 85, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
                stake_grabber.toggle()

                wait(0.3, SECONDS)
                #score the preload
                lift_intake.motor.spin_for(REVERSE, 3, TURNS, 100, PERCENT)
                lift_intake.motor.spin_for(REVERSE, 1, TURNS, 100, PERCENT)

                drivetrain.turn_for(LEFT, 105, DEGREES, 80, PERCENT)

                lift_intake.motor.spin(REVERSE, 100, PERCENT)

                drivetrain.drive_for(FORWARD, 46, INCHES, 90, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 6, INCHES, 90, PERCENT, wait=True)

                drivetrain.turn_for(LEFT, 63, DEGREES, 85, PERCENT, wait=True)

                #just to make sure that the lift intake spins properly
                lift_intake.motor.spin(REVERSE, 100, PERCENT)

                drivetrain.drive_for(FORWARD, 47, INCHES, 90, PERCENT, wait=True)
                drivetrain.drive_for(FORWARD, 7, INCHES, 80, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 6, INCHES, 90, PERCENT)

                #drivetrain.turn_for(RIGHT, 62, DEGREES, 85, PERCENT, wait=True)
                #drivetrain.drive_for(FORWARD, 18, INCHES, 80, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT, wait=True)

                drivetrain.stop()
                
                wait(4, SECONDS)

            elif self.mode == "Goal":
                #its goal rush time
                #BLUE 
                #without alliance stake
                drivetrain.drive_for(REVERSE, 60, INCHES, 85, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
                stake_grabber.toggle()

                wait(0.3, SECONDS)
                #score the preload
                lift_intake.motor.spin_for(REVERSE, 3, TURNS, 100, PERCENT)
                lift_intake.motor.spin_for(REVERSE, 1, TURNS, 100, PERCENT)

                drivetrain.turn_for(RIGHT, 105, DEGREES, 80, PERCENT)

                lift_intake.motor.spin(REVERSE, 100, PERCENT)

                drivetrain.drive_for(FORWARD, 46, INCHES, 90, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 6, INCHES, 90, PERCENT, wait=True)

                drivetrain.turn_for(RIGHT, 63, DEGREES, 85, PERCENT, wait=True)

                #just to make sure that the lift intake spins properly
                lift_intake.motor.spin(REVERSE, 100, PERCENT)

                drivetrain.drive_for(FORWARD, 47, INCHES, 90, PERCENT, wait=True)
                drivetrain.drive_for(FORWARD, 7, INCHES, 80, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 6, INCHES, 90, PERCENT)

                #drivetrain.turn_for(RIGHT, 62, DEGREES, 85, PERCENT, wait=True)
                #drivetrain.drive_for(FORWARD, 18, INCHES, 80, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT, wait=True)

                drivetrain.stop()
                lift_intake.motor.stop(BRAKE)

        elif self.color == BLUE_SIG:
            if self.mode == "Ring":
                #its ring rush time
                #BLUE 
                #without alliance stake
                drivetrain.drive_for(REVERSE, 60, INCHES, 85, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
                stake_grabber.toggle()

                wait(0.3, SECONDS)
                #score the preload
                lift_intake.motor.spin_for(REVERSE, 3, TURNS, 90, PERCENT)
                lift_intake.motor.spin_for(REVERSE, 1, TURNS, 90, PERCENT)
                if lift_intake.motor.velocity() == 0:
                    lift_intake.motor.spin_for(FORWARD, 1,  TURNS, 80, PERCENT, wait=True)

                    lift_intake.motor.spin(REVERSE, 100, PERCENT)
    
                drivetrain.turn_for(RIGHT, 105, DEGREES, 80, PERCENT)

                lift_intake.motor.spin(REVERSE, 100, PERCENT)

                drivetrain.drive_for(FORWARD, 49, INCHES, 90, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 6, INCHES, 90, PERCENT, wait=True)

                drivetrain.turn_for(RIGHT, 63, DEGREES, 85, PERCENT, wait=True)

                #just to make sure that the lift intake spins properly
                lift_intake.motor.spin(REVERSE, 100, PERCENT)

                drivetrain.drive_for(FORWARD, 45, INCHES, 90, PERCENT, wait=True)
                drivetrain.drive_for(FORWARD, 6, INCHES, 80, PERCENT, wait=True)
                lift_intake.motor.spin(REVERSE, 100, PERCENT)
                drivetrain.drive_for(REVERSE, 7, INCHES, 90, PERCENT, wait=True) 

                wait(4, SECONDS)

                #drivetrain.turn_for(LEFT, 62, DEGREES, 85, PERCENT, wait=True)
                #drivetrain.drive_for(FORWARD, 18, INCHES, 80, PERCENT, wait=True)
                #drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT, wait=True)

                #no more moving 
                drivetrain.stop()
                lift_intake.motor.stop(BRAKE)

                #smash into ladder time 
                #drivetrain.turn_for(LEFT, 180, DEGREES, 85, PERCENT, wait=True)
                #drivetrain.drive_for(FORWARD, 56, INCHES, 95, PERCENT)

            elif self.mode == "Goal":
                #its goal rush time
                #BLUE 
                #without alliance stake
                drivetrain.drive_for(REVERSE, 60, INCHES, 85, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
                stake_grabber.toggle()


                wait(0.3, SECONDS)
                #score the preload
                lift_intake.motor.spin_for(REVERSE, 3, TURNS, 100, PERCENT)
                lift_intake.motor.spin_for(REVERSE, 1, TURNS, 100, PERCENT)

                drivetrain.turn_for(LEFT, 105, DEGREES, 80, PERCENT)

                lift_intake.motor.spin(REVERSE, 100, PERCENT)

                drivetrain.drive_for(FORWARD, 46, INCHES, 90, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 6, INCHES, 90, PERCENT, wait=True)

                drivetrain.turn_for(LEFT, 63, DEGREES, 85, PERCENT, wait=True)

                #just to make sure that the lift intake spins properly
                lift_intake.motor.spin(REVERSE, 100, PERCENT)

                drivetrain.drive_for(FORWARD, 47, INCHES, 90, PERCENT, wait=True)
                drivetrain.drive_for(FORWARD, 7, INCHES, 80, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 6, INCHES, 90, PERCENT)

                #drivetrain.turn_for(RIGHT, 62, DEGREES, 85, PERCENT, wait=True)
                #drivetrain.drive_for(FORWARD, 18, INCHES, 80, PERCENT, wait=True)
                drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT, wait=True)

                drivetrain.stop()
                lift_intake.motor.stop(BRAKE)

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

"""def skills(self):
        #initial_time = brain.timer.time(MSEC)
        wall_stake.motor.spin(FORWARD, 90, PERCENT)
        wait(1, SECONDS)
        drivetrain.drive_for(REVERSE, 14, INCHES, 95, PERCENT)
        wall_stake.motor.spin(REVERSE, 90, PERCENT)
        wait(0.9, SECONDS)

        wall_stake.motor.stop(BRAKE)

        drivetrain.drive_for(FORWARD, 8, INCHES, 95, PERCENT)

        drivetrain.turn_for(RIGHT, 80, DEGREES, 90, PERCENT)

        drivetrain.drive_for(REVERSE, 66, INCHES, 95, PERCENT)
        drivetrain.drive_for(REVERSE, 4, INCHES, 95, PERCENT, wait=False)
        stake_grabber.toggle()

        wait(1, SECONDS)

        drivetrain.turn_for(RIGHT, 107, DEGREES, 90, PERCENT)

        lift_intake.spin(REVERSE)

        drivetrain.drive_for(FORWARD, 65, INCHES, 100, PERCENT)

        drivetrain.turn_for(RIGHT, 85, DEGREES, 90, PERCENT)

        drivetrain.drive_for(FORWARD, 62, INCHES, 95, PERCENT)

        drivetrain.turn_for(RIGHT, 85, DEGREES, 90, PERCENT)
        
        drivetrain.drive_for(FORWARD, 74, INCHES, 100, PERCENT)

    #which direction
        drivetrain.drive_for(REVERSE, 62, INCHES, 95, PERCENT, wait=True)
        drivetrain.drive_for(REVERSE, 3, INCHES, 95, PERCENT, wait=False)
        stake_grabber.toggle()

        wait(0.2, SECONDS)
        #score the preload
        lift_intake.motor.spin_for(REVERSE, 3, TURNS, 100, PERCENT)
        lift_intake.motor.spin_for(REVERSE, 1, TURNS, 100, PERCENT)

        drivetrain.turn_for(LEFT, 210, DEGREES, 90, PERCENT)

        lift_intake.motor.spin(REVERSE, 100, PERCENT, wait=False)

        drivetrain.drive_for(FORWARD, 60, INCHES, 95, PERCENT, wait=True)
        wait(0.7, SECONDS)
 
        drivetrain.turn_for(LEFT, 105, DEGREES, 90, PERCENT, wait=True)

        #just to make sure that the lift intake spins properly
        lift_intake.motor.spin(REVERSE, 100, PERCENT, wait=False)

        drivetrain.drive_for(FORWARD, 60, INCHES, 95, PERCENT, wait=True)
        wait(0.7, SECONDS)

        drivetrain.turn_for(LEFT, 105, DEGREES, 90, PERCENT, wait=True)

        lift_intake.motor.spin(REVERSE, 100, PERCENT)

        drivetrain.drive_for(FORWARD, 78, INCHES, 95, PERCENT, wait=True)
        wait(0.3, SECONDS)

        drivetrain.turn_for(LEFT, 305, DEGREES, 90, PERCENT, wait=True)
        drivetrain.drive_for(REVERSE, 60, INCHES, wait=True)

        #ungrab the stake to put into corner
        stake_grabber.toggle()
        wait(0.8, SECONDS)

        drivetrain.drive_for(FORWARD, 60, INCHES, 95, PERCENT, wait=True)

        drivetrain.turn_for(RIGHT, 60, DEGREES, 90, PERCENT, wait=True)

        drivetrain.drive_for(REVERSE, 120, INCHES, 95, PERCENT, wait = True)
        drivetrain.drive_for(REVERSE, 5, INCHES, 95, PERCENT, wait=False)
        
        #to grab second mobile goal
        stake_grabber.toggle()
        
        wait(0.8, SECONDS)

        drivetrain.drive_for(FORWARD, 60, INCHES, 95, PERCENT)
        drivetrain.turn_for(RIGHT, 158, DEGREES, 90, PERCENT, wait=True)

        drivetrain.drive_for(FORWARD, 87, INCHES, 95, PERCENT)
        drivetrain.turn_for(RIGHT, 50, DEGREES, 90, PERCENT)
        drivetrain.drive_for(FORWARD, 15, INCHES, 95, PERCENT)

        drivetrain.turn_for(RIGHT, 305, DEGREES, 90, PERCENT)
        drivetrain.drive_for(REVERSE, 70, INCHES, 95, PERCENT)"""


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

    # TODO: adjust this
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
