#region VEXcode Generated Robot Configuration
from vex import *
import urandom

# Brain should be defined by default
brain=Brain()

# Robot configuration code
back_left = Motor(Ports.PORT1, GearSetting.RATIO_6_1, False)
mid_left = Motor(Ports.PORT2, GearSetting.RATIO_6_1, True)
front_left = Motor(Ports.PORT3, GearSetting.RATIO_6_1, False)
back_right = Motor(Ports.PORT4, GearSetting.RATIO_18_1, True)
mid_right = Motor(Ports.PORT5, GearSetting.RATIO_6_1, False)
front_right = Motor(Ports.PORT6, GearSetting.RATIO_6_1, True)
lift_intake = Motor(Ports.PORT7, GearSetting.RATIO_6_1, False)
# vex-vision-config:begin
vision_sensor__BLUE_SIG = Signature(1, -4645, -3641, -4143,4431, 9695, 7063,2.5, 0)
vision_sensor__RED_SIG = Signature(2, 7935, 9719, 8827,-1261, -289, -775,2.5, 0)
vision_sensor = Vision(Ports.PORT9, 50, vision_sensor__BLUE_SIG, vision_sensor__RED_SIG)
# vex-vision-config:end
stake_grab_left = DigitalOut(brain.three_wire_port.a)
stake_grab_right = DigitalOut(brain.three_wire_port.b)


# wait for rotation sensor to fully initialize
wait(30, MSEC)


# Make random actually random
def initializeRandomSeed():
    wait(100, MSEC)
    random = brain.battery.voltage(MV) + brain.battery.current(CurrentUnits.AMP) * 100 + brain.timer.system_high_res()
    urandom.seed(int(random))
      
# Set random seed 
initializeRandomSeed()


def play_vexcode_sound(sound_name):
    # Helper to make playing sounds from the V5 in VEXcode easier and
    # keeps the code cleaner by making it clear what is happening.
    print("VEXPlaySound:" + sound_name)
    wait(5, MSEC)

# add a small delay to make sure we don't print in the middle of the REPL header
wait(200, MSEC)
# clear the console to make sure we don't have the REPL in the console
print("\033[2J")

#endregion VEXcode Generated Robot Configuration

# ------------------------------------------
# 
# 	Project:      VEXcode Project
#	Author:       VEX
#	Created:
#	Description:  VEXcode V5 Python Project
# 
# ------------------------------------------

# Library imports
from vex import *

# Begin project code
left_drive = MotorGroup(back_left, mid_left, front_left)
right_drive = MotorGroup(back_right, mid_right, front_right)
drivetrain = DriveTrain(left_drive, right_drive, 319.19, 295, 40, MM, 1)

