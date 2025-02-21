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

            # Hold on, I found something. Let's wait until the switch is hit.
            timer = 0
            akita_neru = False

            while not self.limit_switch.pressing():
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

            save_direction = lift_intake._get_direction()

            wait(100)
            lift_intake.motor.spin_for(REVERSE, 180, DEGREES, 70, PERCENT, True)
            print("Gooned!")
            wait(250)

            lift_intake.spin(save_direction)

class DigitalOutToggleable(DigitalOut):
    def __init__(self, port, default_state=False):
        super().__init__(port)

        self.state = default_state

    def toggle(self):
        self.state = not self.state
        self.set(self.state)
    
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

def do_drive_loop() -> None:
    accel_stick = controller.axis3.position()
    turn_stick = controller.axis1.position()

    lm.spin(FORWARD, accel_stick - turn_stick, PERCENT)
    rm.spin(FORWARD, accel_stick + turn_stick, PERCENT)


def driver():
    init()
    while True:
        do_drive_loop()
        wait(1 / 60, SECONDS)

config_auton_direction = LEFT
def auton_match():
    global config_auton_direction

    lift_intake.stop()

    wait(0.5, SECONDS)

    wall_stake.score()
    drivetrain.drive_for(REVERSE, 20, INCHES, 80, PERCENT)

    drivetrain.turn_for(config_auton_direction, 90, DEGREES, 85, wait=True)

    lift_intake.spin(FORWARD)

    drivetrain.drive_for(FORWARD, 85, INCHES, 90, PERCENT)

def auton_skills():
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
        competiton = Competition(driver, auton_match)
    else:
        competiton = Competition(driver, auton_skills)

    driver()

def main():
    menu = SelectionMenu()

    menu.add_option("Team color", Color.RED, ["Red", "Blue"])
    menu.add_option("Auton direction", Color.BLUE, ["Left", "Right"])
    menu.add_option("Auton type", Color.YELLOW, ["Match", "Skills"])

    menu.on_enter(start)
    menu.draw()

if __name__ == "__main__":
    main()    
