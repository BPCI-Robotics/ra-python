from vex import *

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
    def __init__(self, motor: Motor):
        self.motor = motor
        self.motor.set_stopping(HOLD)
        self.absolute0Position = self.motor.position(DEGREES)

    #any of the following functions may be changed to self.motor.spin_for(FORWARD, 70, DEGREES, 60, RPM)
    def pickup(self):
        self.motor.spin_to_position(50, DEGREES, 60, RPM)
            
    def hold(self):
        self.motor.spin_to_position(140, DEGREES, 60, RPM)
        
    def score(self):
        self.motor.spin_to_position(300, DEGREES, 70, RPM)

    def reset(self):
        self.motor.spin_to_position(self.absolute0Position, DEGREES, 70, RPM)

class LiftIntake:
    def __init__(self, motor: Motor, vision: Vision, limit_switch: Limit):
        self.motor = motor
        self.vision = vision
        self.limit_switch = limit_switch

        self.running = False
        self.sorting_enabled = True
        self.enemy_sig = RED_SIG

        self.motor.set_stopping(BRAKE)
        Thread(self._sorting_loop)
    
    def set_enemy_sig(self, sig: Signature):
        self.enemy_sig = sig

    def spin(self, direction: DirectionType.DirectionType):
        self.running = True
        self.motor.spin(direction, 100, PERCENT)
    
    def _get_direction(self):
        return self.motor.direction()

    def stop(self):
        self.running = False
        self.motor.stop()

    def _sorting_loop(self):

        while True:
            sleep(20, MSEC)

            # Exit: the lift intake isn't running or the user doesn't want to color sort.
            if not self.running or not self.sorting_enabled:
                continue

            enemy_donut = self.vision.take_snapshot(self.enemy_sig, 1)

            if enemy_donut:
                enemy_donut = enemy_donut[0]
            else:
                continue

            # Exit: the donut is too far away (so it appears small)
            if enemy_donut.height < 30 or enemy_donut.width < 70:
                continue
            
            print("Found an enemy donut.")
            print("Waiting for switch to be hit.")

            # Hold on, I found something. Let's wait until the switch is hit.
            while not self.limit_switch.pressing():
                wait(15)

                if not self.sorting_enabled:
                    break
            
            print("Switch was hit.")

            # Exit: Driver turned off color sort.
            if (not self.sorting_enabled):
                continue

            save_direction = lift_intake._get_direction()

            print("I think donut got to top")
            wait(25, MSEC)
            lift_intake.stop()
            lift_intake.spin(REVERSE)
            print("I went backwards!")
            wait(1300, MSEC)
            print("Done")
            print("")

            lift_intake.spin(save_direction)

class DigitalOutToggleable(DigitalOut):
    def __init__(self, port, default_state=False):
        super().__init__(port)

        self.state = default_state

    def toggle(self):
        self.state = not self.state
        self.set(self.state)

#region Parts
BLUE_SIG = Signature(1, -4645, -3641, -4143,4431, 9695, 7063, 2.5, 0)
RED_SIG = Signature(2, 7935, 9719, 8827,-1261, -289, -775, 2.5, 0)

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

stake_grabber = DigitalOutToggleable(brain.three_wire_port.a)
doink_piston = DigitalOutToggleable(brain.three_wire_port.b)

drivetrain= DriveTrain(
                lm,
                rm,
                259.34, # wheel travel
                310,    # track width
                205,     # wheel base
                MM,     # unit
                600/360 
            )

lift_intake = LiftIntake(
    Motor(Ports.PORT7, GearSetting.RATIO_6_1, True), 
    Vision(Ports.PORT9, 50, BLUE_SIG, RED_SIG), 
    Limit(brain.three_wire_port.c)
)

wall_stake = WallStake(Motor(Ports.PORT8, GearSetting.RATIO_36_1, True))

#endregion Parts

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

    controller.buttonR2.pressed(stake_grabber.toggle)
    controller.buttonR1.pressed(doink_piston.toggle)

def driver():
    init()
    while True:
        accel_stick = controller.axis3.position()
        turn_stick = controller.axis1.position()

        lm.spin(FORWARD, accel_stick - turn_stick, PERCENT)
        rm.spin(FORWARD, accel_stick + turn_stick, PERCENT)

        wait(1 / 60, SECONDS)

config_auton_direction = LEFT

def auton_quals():
    global config_auton_direction
    
    if config_auton_direction == LEFT:
        #run ring rush with alliance stake scoring

        drivetrain.drive_for(FORWARD, 25, INCHES, 80, PERCENT, True)
        drivetrain.turn_for(LEFT, 150, DEGREES, 75, PERCENT, True)
        drivetrain.drive_for(FORWARD, 2, INCHES, 60, PERCENT, True)
        drivetrain.drive_for

        #give some time to stabilize
        wait(0.2, SECONDS)

        wall_stake.score()

        wait(0.5, SECONDS)

        drivetrain.drive_for(FORWARD, 10, INCHES, 90, PERCENT, True)

        drivetrain.turn_for(LEFT, 91.6, DEGREES, 80, PERCENT)

        drivetrain.drive_for(REVERSE, 55, INCHES, 90, PERCENT, True)
        drivetrain.drive_for(FORWARD, 5, INCHES, 80, PERCENT, True)
        stake_grabber.toggle()

        wait(0.2, SECONDS)

        drivetrain.turn_for(RIGHT, 200, DEGREES, 85, PERCENT, True)

        lift_intake._sorting_loop()
        drivetrain.drive_for(FORWARD, 34, INCHES, 90, PERCENT, True)
        drivetrain.drive_for(REVERSE, 5, INCHES, 80, PERCENT, True)
        #after testing, we can add the above two lines again to pick up a third donut onto the stake

        drivetrain.turn_for(RIGHT, 150, DEGREES, 80, PERCENT)

        drivetrain.drive_for(FORWARD, 30, INCHES, 90, PERCENT, True)
        drivetrain.drive_for(REVERSE, 5, INCHES, 80, PERCENT, True)

        #check the time - if we don't have much time left, then just hit ladder
        drivetrain.turn_for(RIGHT, 150, DEGREES, 85, PERCENT, True)
        drivetrain.drive_for(FORWARD, 60, INCHES, 90, PERCENT)

        #check the time - if we have time left, then the following code will apply

        #drivetrain.turn_for(LEFT, 150, DEGREES, 75, PERCENT, True)

        #drivetrain.drive_for(FORWARD, 51, INCHES, 90, PERCENT, True)
        
        #doink_piston.toggle()
        #drivetrain.drive_for(FORWARD, 10, INCHES, 80, PERCENT)
        #drivetrain.turn_for(LEFT, 116.6, DEGREES, 90, PERCENT)

    elif config_auton_direction == RIGHT:
        #ts for goal rush
        drivetrain.drive_for(REVERSE, 40, INCHES, 85, PERCENT, True)
        drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
        stake_grabber.toggle()

        wait(0.3, SECONDS)
        #score the preload
        lift_intake.motor.spin_for(REVERSE, 2, TURNS, True)
        lift_intake.motor.spin_for(REVERSE, 1, TURNS)
        drivetrain.turn_for(LEFT, 150, DEGREES, 80, PERCENT, True)

        lift_intake._sorting_loop()

        drivetrain.drive_for(FORWARD, 35, INCHES, 90, PERCENT, True)
        wait(0.5, SECONDS)
        drivetrain.drive_for(REVERSE, 5, INCHES, 80, PERCENT, True)

        drivetrain.turn_for(RIGHT, 150, DEGREES, 85, PERCENT, True)
        drivetrain.drive_for(FORWARD, 12, INCHES, 90, PERCENT, True)

        drivetrain.turn_for(LEFT, 150, DEGREES, 85, PERCENT, True)
        drivetrain.drive_for(FORWARD, 18, INCHES, 90, PERCENT, True)

        drivetrain.turn_for(RIGHT, 150, DEGREES, 85, PERCENT, True)

        drivetrain.drive_for(FORWARD, 60, INCHES, 90, PERCENT, True)
        
        #clear corner
        doink_piston.toggle()
        drivetrain.drive_for(FORWARD, 10, INCHES, 80, PERCENT)
        drivetrain.turn_for(RIGHT, 116.6, DEGREES, 90, PERCENT)




def auton_elims():
    global config_auton_direction

    if config_auton_direction == LEFT:
        #its ring rush time
        #without alliance stake
        drivetrain.drive_for(REVERSE, 40, INCHES, 85, PERCENT, True)
        drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
        stake_grabber.toggle()

        wait(0.3, SECONDS)
        #score the preload
        lift_intake.motor.spin_for(REVERSE, 2, TURNS, True)
        lift_intake.motor.spin_for(REVERSE, 1, TURNS)
        drivetrain.turn_for(RIGHT, 150, DEGREES, 80, PERCENT, True)

        lift_intake._sorting_loop()
        drivetrain.drive_for(FORWARD, 20, INCHES, True)
        drivetrain.drive_for(REVERSE, 4, INCHES, True)

        drivetrain.turn_for(RIGHT, 150, DEGREES, 85, PERCENT, True)
        #"thrust" the donuts
        drivetrain.drive_for(FORWARD, 18, INCHES, 85, PERCENT, True)
        drivetrain.drive_for(REVERSE, 7, INCHES, 85, PERCENT, True)
        drivetrain.turn_for(LEFT, 150, DEGREES, 85, PERCENT, True)
        drivetrain.drive_for(FORWARD, 8, INCHES, 85, PERCENT, True)
        drivetrain.turn_for(RIGHT, 150, DEGREES, 85, PERCENT, True)
        drivetrain.drive_for(FORWARD, 8, INCHES, 80, PERCENT, True)
        drivetrain.drive_for(REVERSE, 8, INCHES, 85, PERCENT, True)

        drivetrain.turn_for(LEFT, 150, DEGREES, 75, PERCENT, True)
        drivetrain.drive_for(FORWARD, 14, INCHES, 90, PERCENT, True)
        drivetrain.turn_for(LEFT, 150, DEGREES, 85, PERCENT, True)

        drivetrain.drive_for(FORWARD, 51, INCHES, 90, PERCENT, True)
        
        doink_piston.toggle()
        drivetrain.drive_for(FORWARD, 10, INCHES, 80, PERCENT)
        drivetrain.turn_for(LEFT, 116.6, DEGREES, 90, PERCENT)
        
    elif config_auton_direction == RIGHT:
        #ts for goal rush again
        drivetrain.drive_for(REVERSE, 40, INCHES, 85, PERCENT, True)
        drivetrain.drive_for(REVERSE, 5, INCHES, 85, PERCENT)
        stake_grabber.toggle()

        wait(0.3, SECONDS)
        #score the preload
        lift_intake.motor.spin_for(REVERSE, 2, TURNS, True)
        lift_intake.motor.spin_for(REVERSE, 1, TURNS)
        drivetrain.turn_for(LEFT, 150, DEGREES, 80, PERCENT, True)

        lift_intake._sorting_loop()

        drivetrain.drive_for(FORWARD, 35, INCHES, 90, PERCENT, True)
        wait(0.5, SECONDS)
        drivetrain.drive_for(REVERSE, 5, INCHES, 80, PERCENT, True)

        drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT, True)
        drivetrain.drive_for(FORWARD, 12, INCHES, 90, PERCENT, True)

        drivetrain.turn_for(LEFT, 90, DEGREES, 85, PERCENT, True)
        drivetrain.drive_for(FORWARD, 18, INCHES, 90, PERCENT, True)

        drivetrain.turn_for(RIGHT, 90, DEGREES, 85, PERCENT, True)

        drivetrain.drive_for(FORWARD, 60, INCHES, 90, PERCENT, True)
        
        #clear corner
        doink_piston.toggle()
        drivetrain.drive_for(FORWARD, 10, INCHES, 80, PERCENT)
        drivetrain.turn_for(RIGHT, 70, DEGREES, 90, PERCENT)


def auton_skills():
    #routine plan
    #no color sorting involved btw
    pass

def start(config: dict[str, Any]):

    global config_auton_direction

    if config["Team color"] == "Red":
        lift_intake.set_enemy_sig(BLUE_SIG)
    else:
        lift_intake.set_enemy_sig(RED_SIG)
    
    if config["Auton direction"] == "Left":
        config_auton_direction = LEFT
    else:
        config_auton_direction = RIGHT
    
    if config["Auton type"] == "Match":
        if config['Match type'] == "Quals":
            competition = Competition(driver, auton_quals)
        elif config['Match type'] == "Elims":
            competition = Competition(driver, auton_elims)
    else:
        competition = Competition(driver, auton_skills)
    
    if not competition.is_field_control() and not competition.is_competition_switch():
        if config["Testing"] == "Auton":
            if config["Auton type"] == "Match":
                if config["Match type"] == "Quals":
                    auton_quals()
                elif config["Match type"] == "Elims":
                    auton_elims()
            else:
                auton_skills()
        else:
            driver()

def main():
    menu = SelectionMenu()

    menu.add_option("Team color", Color.RED, ["Red", "Blue"])
    menu.add_option("Auton direction", Color.BLUE, ["Left", "Right"])
    menu.add_option("Match type", Color.PURPLE, ["Quals", "Elims"])
    menu.add_option("Auton type", Color.YELLOW, ["Match", "Skills"])
    menu.add_option("Testing", Color.CYAN, ["Driver Control", "Auton"])

    menu.on_enter(start)
    
    menu.draw()
    print("\033[2J")
    controller.buttonLeft.pressed(menu.force_submit)

if __name__ == "__main__":
    main()    


        
