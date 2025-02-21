from vex import *
brain = Brain()

class PID_Drivetrain:
    class _PID_Basic:
        def __init__(self, PID: tuple[float, float, float]):
            self.Kp = PID[0]
            self.Ki = PID[1]
            self.Kd = PID[2]

            self.time_prev = 0
            self.e_prev = 0

        def __call__(self, current: float, target: float) -> float:
            
            self.target = target
            self.current = current
            return self._do_calculation()

        def _do_calculation(self) -> float:

            Kp = self.Kp
            Ki = self.Ki
            Kd = self.Kd
            I = 0

            time = brain.timer.time(MSEC) / 1000

            e = self.target - self.current

            P = Kp*e
            I += Ki*e*(time - self.time_prev)
            D = Kd*(e - self.e_prev)/(time - self.time_prev)

            MV = P + I + D

            self.e_prev = e
            self.time_prev = time

            return self.current + MV
    
    def __init__(self, turn_kPID: tuple[float, float, float], drive_kPID: tuple[float, float, float], 
                       drivetrain: DriveTrain):
        
        self.dt = drivetrain

        self.turn_pid = self._PID_Basic(turn_kPID)
        self.drive_pid = self._PID_Basic(drive_kPID)
    
    def get_turn_velocity(self) -> float:
        return (self.dt.lm.velocity(PERCENT) - self.dt.rm.velocity(PERCENT)) / 2

    def turn_for(self, direction: TurnType, angle: vexnumber, units: RotationUnits.RotationUnits):

        self.dt.turn_for(direction, angle, units, wait=False)

        while self.dt.is_moving():
            self.dt.set_turn_velocity(self.turn_pid(self.get_turn_velocity(), target=85), PERCENT)
    
    def drive_for(self, direction: DirectionType, distance: vexnumber, units: DistanceUnits.DistanceUnits):

        self.dt.drive_for(direction, distance * (3 / 4), units)

        while self.dt.is_moving():
            self.dt.set_drive_velocity(self.drive_pid(self.dt.velocity(PERCENT), 85), PERCENT)