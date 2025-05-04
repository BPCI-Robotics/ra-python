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

# TODO: Test PID
class WallStake:
    def __init__(self, motor: Motor, rotation: Rotation):
        self.motor = motor
        self.rotation = rotation

        self.motor.set_stopping(HOLD)
        self.rotation.reset_position()
        self.target_pos = 0
    
    def spin_to(self, target, unit, timeout=1000):
        time_spent = 0
        while abs(target - self.rotation.position(unit)) > 5 and time_spent < timeout:

            #if self.motor.torque(TorqueUnits.NM) > 0.1:
                #break

            if target > self.rotation.position(unit):
                self.motor.spin(FORWARD, 40, PERCENT)
            
            if target < self.rotation.position(unit):
                self.motor.spin(REVERSE, 40, PERCENT)

            wait(20, MSEC)
            time_spent += 20
        
        self.motor.stop()

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

    def limiter(self):
        while True:
            wait(20, MSEC)
            if self.rotation.position(DEGREES) > 120:
                self.motor.stop(HOLD)

    def constantly_limiting(self):
        Thread(self.limiter)

# COMPLETED
class LiftIntake:
    def __init__(self, motor: Motor):
        self.motor = motor
        self.enemy_sig = None

        self.motor.set_stopping(BrakeType.BRAKE)
        self.spinning = False

    def spin(self, direction: DirectionType.DirectionType):
        self.motor.spin(direction, 100, PERCENT)
        self.spinning = True
    
    def get_unstuck(self):
        while self.spinning == True:
            wait(20, MSEC)
            if self.motor.velocity(RPM) == 0:
                self.motor.spin(FORWARD)
                wait(0.3, SECONDS)
                self.spin(REVERSE)

            else:
                continue

    def constantly_unstuck(self):
        Thread(self.get_unstuck)


    def stop(self):
        self.motor.stop()
        self.spinning = False


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

#This function is actually stupid. Dumb bunny #1 and Dumb bunny #2 had a brainfart here 
#until Dumb bunny #2 turned into Srinivasa Ramanujan and came up with an elliptic curve 
#approximation algorithm that was pulled straight from his bowels
def scale(n):
    return n / 0.352

# THIS ONLY RETURNS INCHES!!
def tiles(n):
    return scale(n * 24)

#Note: ts is the Ramanujan approximation which Dumb bunny #2 came up with. 
#This is probably what we wanted in the first place, but we were actually stupid.
def scale_degrees(n):
    return (1/(1-0.352))*n

def scale_distance(n):
    return (1/0.352)*n

class Auton:
    def __init__(self):
        self.direction = LEFT
        self._routine_selected = self._noop
        self.color = RED_SIG
        self.mode = "Ring"

        #drivetrain.set_heading(0, DEGREES)
        #drivetrain.set_rotation(0, DEGREES)
        drivetrain.set_turn_velocity(75, PERCENT)
        drivetrain.set_drive_velocity(60, PERCENT)
        drivetrain.set_stopping(COAST)

    def _noop(self):
        raise ValueError("auton was not set.")

    def _skills(self):
        initialize()
        drivetrain.drive_for(FORWARD, scale_distance(10.5), INCHES, 80, PERCENT)
        wall_stake.spin_to(117, DEGREES)
        wait(1, SECONDS)
        drivetrain.drive_for(REVERSE, scale_distance(3), INCHES, 80, PERCENT)
        wall_stake.reset()
        drivetrain.drive_for(REVERSE, scale_distance(4), INCHES, 80, PERCENT)
        if wall_stake.rotation.position() > 0:
            wall_stake.reset()
        
        drivetrain.drive_for(REVERSE, scale_distance(5), INCHES, 80, PERCENT)
        drivetrain.turn_for(LEFT, scale_degrees(90), DEGREES, 80, PERCENT)
        drivetrain.drive_for(REVERSE, scale_distance(26), INCHES, 80, PERCENT)
        stake_grabber.toggle()
        lift_intake.spin(REVERSE)
        lift_intake.constantly_unstuck()
        drivetrain.drive_for(REVERSE, scale_distance(4), INCHES, 80, PERCENT)
        drivetrain.turn_for(LEFT, scale_degrees(91), DEGREES, 80, PERCENT)
        drivetrain.drive_for(FORWARD, scale_distance(28), INCHES, 85, PERCENT)
        wait(0.4, SECONDS)
        drivetrain.turn_for(LEFT, scale_degrees(91), DEGREES, 85, PERCENT)
        drivetrain.drive_for(FORWARD, scale_distance(28), INCHES, 90, PERCENT)
        wait(0.4, SECONDS)
        drivetrain.turn_for(LEFT, scale_degrees(64), DEGREES, 90, PERCENT)
        drivetrain.drive_for(FORWARD, scale_distance(28), INCHES, 95, PERCENT)
        wait(0.4, SECONDS)
        drivetrain.drive_for(REVERSE, scale_distance(14), INCHES, 95, PERCENT)
        drivetrain.turn_for(LEFT, scale_degrees(29), DEGREES, 95, PERCENT)
        drivetrain.drive_for(FORWARD, scale_distance(29), INCHES, 100, PERCENT)
        drivetrain.turn_for(LEFT, scale_degrees(110), DEGREES, 100, PERCENT)
        drivetrain.drive_for(REVERSE, scale_distance(34), INCHES, 90, PERCENT)
        stake_grabber.toggle()
        drivetrain.drive_for(FORWARD, scale_distance(10), INCHES, 85, PERCENT)

        
    def _quals(self):
        if self.color == RED_SIG:
            if self.mode == "Ring":
                initialize()
                drivetrain.drive_for(FORWARD, scale_distance(11.5), INCHES, 60, PERCENT, True)
                wait(0.25, SECONDS)
                wall_stake.spin_to(120, DEGREES)  
                wait(0.85, SECONDS)
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, False)
                wall_stake.spin_to(125, DEGREES)
                wait(0.2, SECONDS)
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, True)          
                wall_stake.reset()
                drivetrain.drive_for(REVERSE, tiles(1.4), INCHES, 60, PERCENT, True)

                if wall_stake.rotation.position(DEGREES) > 0:
                    wall_stake.reset()
                
                #grab stake
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.spin(REVERSE)
                lift_intake.constantly_unstuck()
                drivetrain.turn_for(LEFT, scale_degrees(183), DEGREES, 80, PERCENT)

                wait(0.5, SECONDS)
                drivetrain.drive_for(FORWARD, scale_distance(24), INCHES, 70, PERCENT)
                wait(0.16, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(18), INCHES, 70, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(52), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(15), INCHES, 80, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(5), INCHES, 80, PERCENT)
                drivetrain.turn_for(LEFT, scale_degrees(70), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(14), INCHES, 70, PERCENT)
                wait(0.17, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(20), INCHES, 70, PERCENT)
                drivetrain.turn_for(LEFT, scale_degrees(72), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(24), INCHES, 80, PERCENT)

            elif self.mode == "Goal":
                initialize()
                drivetrain.drive_for(FORWARD, scale_distance(11.5), INCHES, 70, PERCENT)
                wait(0.25, SECONDS)
                wall_stake.spin_to(115, DEGREES)
                wait(0.85, SECONDS)  
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, True)
                wall_stake.reset()
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT)
                drivetrain.drive_for(REVERSE, tiles(1.45), INCHES, 60, PERCENT)
                
                if wall_stake.rotation.position(DEGREES) > 0:
                    wall_stake.reset()
                
                wait(0.2, SECONDS)
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.spin(REVERSE)
                lift_intake.constantly_unstuck()
                drivetrain.turn_for(RIGHT, scale_degrees(139), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(22), INCHES, 80, PERCENT)
                wait(0.5, SECONDS)
                drivetrain.turn_for(LEFT, scale_degrees(182), DEGREES, 85, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(44), INCHES, 85, PERCENT)
                
                wait(0.6, SECONDS)

                lift_intake.stop()

        elif self.color == BLUE_SIG:
            if self.mode == "Ring":
                initialize()
                drivetrain.drive_for(FORWARD, scale_distance(11.5), INCHES, 60, PERCENT, True)
                wait(0.25, SECONDS)
                wall_stake.spin_to(120, DEGREES)  
                wait(0.85, SECONDS)
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, False)
                wall_stake.spin_to(125, DEGREES)
                wait(0.2, SECONDS)
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, True)          
                wall_stake.reset()
                drivetrain.drive_for(REVERSE, tiles(1.4), INCHES, 60, PERCENT, True)

                if wall_stake.rotation.position(DEGREES) > 0:
                    wall_stake.reset()

                #grab stake
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.spin(REVERSE)
                lift_intake.constantly_unstuck()
                drivetrain.turn_for(RIGHT, scale_degrees(183), DEGREES, 80, PERCENT)

                wait(0.5, SECONDS)
                drivetrain.drive_for(FORWARD, scale_distance(24), INCHES, 70, PERCENT)
                wait(0.16, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(18), INCHES, 70, PERCENT)
                drivetrain.turn_for(LEFT, scale_degrees(52), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(15), INCHES, 80, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(5), INCHES, 80, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(66), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(15), INCHES, 70, PERCENT)
                wait(0.17, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(21), INCHES, 70, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(68), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(24), INCHES, 80, PERCENT)

                lift_intake.stop()

            
            elif self.mode == "Goal":
                initialize()
                drivetrain.drive_for(FORWARD, scale_distance(11.5), INCHES, 70, PERCENT)
                wait(0.25, SECONDS)
                wall_stake.spin_to(118, DEGREES)
                wait(0.85, SECONDS)  
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, True)
                wall_stake.reset()
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT)
                drivetrain.drive_for(REVERSE, tiles(1.45), INCHES, 60, PERCENT)
                
                if wall_stake.rotation.position(DEGREES) > 0:
                    wall_stake.reset()
                
                wait(0.2, SECONDS)
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.spin(REVERSE)
                lift_intake.constantly_unstuck()
                drivetrain.turn_for(LEFT, scale_degrees(141), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(22), INCHES, 80, PERCENT)
                wait(0.5, SECONDS)
                drivetrain.turn_for(LEFT, scale_degrees(182), DEGREES, 85, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(41), INCHES, 85, PERCENT)
                
                wait(0.6, SECONDS)

                lift_intake.stop()

    
    
    
    def _elims(self):
        drivetrain.set_timeout(5, SECONDS)
        if self.color == RED_SIG:
            if self.mode == "Ring":
                initialize()
                drivetrain.drive_for(FORWARD, scale_distance(11.5), INCHES, 60, PERCENT, True)
                wait(0.25, SECONDS)
                wall_stake.spin_to(120, DEGREES)  
                wait(0.85, SECONDS)
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, False)
                wall_stake.spin_to(125, DEGREES)
                wait(0.2, SECONDS)
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, True)          
                wall_stake.reset()
                drivetrain.drive_for(REVERSE, tiles(1.4), INCHES, 60, PERCENT, True)

                if wall_stake.rotation.position(DEGREES) > 0:
                    wall_stake.reset()
                
                #grab stake
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.spin(REVERSE)
                lift_intake.constantly_unstuck()
                drivetrain.turn_for(LEFT, scale_degrees(183), DEGREES, 80, PERCENT)

                wait(0.5, SECONDS)
                drivetrain.drive_for(FORWARD, scale_distance(24), INCHES, 70, PERCENT)
                wait(0.16, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(18), INCHES, 70, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(52), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(15), INCHES, 80, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(5), INCHES, 80, PERCENT)
                drivetrain.turn_for(LEFT, scale_degrees(70), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(14), INCHES, 70, PERCENT)
                wait(0.17, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(29), INCHES, 85, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(48), DEGREES, 80, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(25), INCHES, 90, PERCENT)

            elif self.mode == "Goal":
                initialize()
                drivetrain.drive_for(FORWARD, scale_distance(11.5), INCHES, 70, PERCENT)
                wait(0.25, SECONDS)
                wall_stake.spin_to(115, DEGREES)
                wait(0.85, SECONDS)  
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, True)
                wall_stake.reset()
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT)
                drivetrain.drive_for(REVERSE, tiles(1.45), INCHES, 60, PERCENT)
                
                if wall_stake.rotation.position(DEGREES) > 0:
                    wall_stake.reset()
                
                wait(0.2, SECONDS)
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.spin(REVERSE)
                lift_intake.constantly_unstuck()
                drivetrain.turn_for(RIGHT, scale_degrees(140), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(22), INCHES, 80, PERCENT)
                wait(0.35, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(24), INCHES, 80, PERCENT)
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                drivetrain.drive_for(FORWARD, scale_distance(2), INCHES, 85, PERCENT)
                drivetrain.turn_for(LEFT, scale_degrees(136), DEGREES, 85, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(30), INCHES, 80, PERCENT)
                lift_intake.stop()
                stake_grabber.toggle()
                wait(0.4, SECONDS)
                drivetrain.drive_for(FORWARD, scale_distance(8), INCHES, 80, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(126), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(21), INCHES, 95, PERCENT)

        elif self.color == BLUE_SIG:
            if self.mode == "Ring":
                initialize()
                drivetrain.drive_for(FORWARD, scale_distance(11.5), INCHES, 60, PERCENT, True)
                wait(0.25, SECONDS)
                wall_stake.spin_to(120, DEGREES)  
                wait(0.85, SECONDS)
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, False)
                wall_stake.spin_to(125, DEGREES)
                wait(0.2, SECONDS)
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, True)          
                wall_stake.reset()
                drivetrain.drive_for(REVERSE, tiles(1.4), INCHES, 60, PERCENT, True)

                if wall_stake.rotation.position(DEGREES) > 0:
                    wall_stake.reset()


                #grab stake
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.spin(REVERSE)
                lift_intake.constantly_unstuck()
                drivetrain.turn_for(RIGHT, scale_degrees(183), DEGREES, 80, PERCENT)

                wait(0.5, SECONDS)
                drivetrain.drive_for(FORWARD, scale_distance(24), INCHES, 70, PERCENT)
                wait(0.16, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(18), INCHES, 70, PERCENT)
                drivetrain.turn_for(LEFT, scale_degrees(52), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(15), INCHES, 80, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(5), INCHES, 80, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(66), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(15), INCHES, 70, PERCENT)
                wait(0.17, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(31), INCHES, 70, PERCENT)
                lift_intake.stop()
                drivetrain.turn_for(LEFT, scale_degrees(48), DEGREES, 80, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(30), INCHES, 90, PERCENT)
                

            elif self.mode == "Goal":
                initialize()
                drivetrain.drive_for(FORWARD, scale_distance(11.5), INCHES, 70, PERCENT)
                wait(0.25, SECONDS)
                wall_stake.spin_to(118, DEGREES)
                wait(0.85, SECONDS)  
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT, True)
                wall_stake.reset()
                drivetrain.drive_for(REVERSE, 6, INCHES, 70, PERCENT)
                drivetrain.drive_for(REVERSE, tiles(1.45), INCHES, 60, PERCENT)
                
                if wall_stake.rotation.position(DEGREES) > 0:
                    wall_stake.reset()
                
                wait(0.2, SECONDS)
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.spin(REVERSE)
                lift_intake.constantly_unstuck()
                drivetrain.turn_for(LEFT, scale_degrees(141), DEGREES, 80, PERCENT)
                drivetrain.drive_for(FORWARD, scale_distance(22), INCHES, 80, PERCENT)
                wait(0.4, SECONDS)
                drivetrain.drive_for(REVERSE, scale_distance(24), INCHES, 85, PERCENT)
                wait(0.5, SECONDS)
                stake_grabber.toggle()
                wait(0.2, SECONDS)
                lift_intake.stop()
                drivetrain.drive_for(FORWARD, scale_distance(3), INCHES, 90, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(129), DEGREES, 90, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(31), INCHES, 90, PERCENT)
                stake_grabber.toggle()
                drivetrain.drive_for(FORWARD, scale_distance(10), INCHES, 80, PERCENT)
                drivetrain.turn_for(RIGHT, scale_degrees(61), DEGREES, 95, PERCENT)
                drivetrain.drive_for(REVERSE, scale_distance(28), INCHES, 90, PERCENT)

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
        #wall_stake.start_log()
        self._routine_selected()


#region Parts
brain = Brain()
controller = Controller()

stake_grabber = DigitalOutToggleable(brain.three_wire_port.a)
doink_piston = DigitalOutToggleable(brain.three_wire_port.b)

inertial = Inertial(Ports.PORT10)

drivetrain= DriveTrain(
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

                #inertial, 

                259.34, # wheel travel
                315,    # track width
                280,    # wheel base
                MM,     # unit
                600/360 # gear ratio
            )
d = drivetrain

lift_intake = LiftIntake(Motor(Ports.PORT7, GearSetting.RATIO_6_1, True))

# TODO: tune the PID
wall_stake_PID_constants = (0.3, 0.0, 0.1)
wall_stake = WallStake(Motor(Ports.PORT8, GearSetting.RATIO_36_1, True), Rotation(Ports.PORT9, True))

#endregion Parts

def initialize():
    inertial.calibrate()
    # drivetrain.set_turn_direction_reverse(True)

    # TODON'T: adjust this (I don't know what it does)
    # drivetrain.set_turn_constant(1)

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
    wall_stake.constantly_limiting()
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
