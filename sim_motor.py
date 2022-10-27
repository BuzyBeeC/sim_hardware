'''A simulated stepper motor/MotorController for testing purposes

A lot of code is shared with motor_control.py's MotorController for similar behavior
'''
MSTEP_PIN_STATES = {
    (False, False): 1,
    (True, False): 2,
    (False, True): 4,
    (True, True): 8
}

def _closestLoopMovement(currPos: int, newPos: int, loopSize: int) -> int:
    '''In a closed loop of positive integers (imagine modulo) of size `loopSize`,
    this will calculate the closest relative movement to reach `newPos` from `currPos`.

    Note: Because this movement is relative, a directionally signed value is returned.
    You may need to clamp values that you sum with this.'''
    currPos %= loopSize
    newPos %= loopSize
    if (currPos == newPos): return 0

    upper = lower = newPos
    if newPos < currPos:
        upper += loopSize
    else:
        lower -= loopSize

    return int((lower - currPos) if ((currPos - lower) < (upper - currPos)) else (upper - currPos))

class vMotor:
    _id_count = 1 

    def __init__(self, pins: tuple[int, int, int | None, int | None],
                 stepsPerRev: int = 200, gearRatio: float = 1, name: str | None = None):
        '''Create a vMotor object

        `pins`: pin/BCM GPIO numbers (step, dir, ms1, ms2)
        `stepsPerRev`: number of full steps per 1 full revolution of the motor
        `gearRatio` (optional): gear ratio to an output gear; defaults to 1
        `name` (optional): will autogenerate name if None provided
        '''
        self._msteps: int = 0
        self._mstepMode: int = 1
        self._gearRatio: float = gearRatio
        self._dir = 1  # 1 for CW and -1 for CCW
        self._hasMoved = False

        self.PINS: dict[str, int | None] = {name: pin
                                            for name, pin
                                            in zip(("step", "dir", "ms1", "ms2"), pins)}
        self.STEPS_PER_REV = stepsPerRev
        self.name: str = name if name is not None else ("vMotor " + str(vMotor._id_count))

        vMotor._id_count += 1

    def mstepsToDegrees(self, numMsteps) -> float:
        return float((numMsteps * 360) / (self.STEPS_PER_REV * self._mstepMode))

    def degreesToMsteps(self, deg, useGearOut: bool = False) -> int:
        if useGearOut:
            return int((deg * self._gearRatio * self.STEPS_PER_REV * self._mstepMode) / 360)
        return int((deg * self.STEPS_PER_REV * self._mstepMode) / 360) 

    @property
    def steps(self) -> int:
        '''vMotor's position in full steps. (0 <= steps < steps per rotation)'''
        return int(self._msteps / self._mstepMode)

    @property
    def msteps(self) -> int:
        '''vMotor's position in microsteps. (0 <= msteps < msteps per rotation)'''
        return self._msteps

    @property
    def degrees(self) -> float:
        '''vMotor's position in degrees.'''
        return float(self.mstepsToDegrees(self._msteps))
    
    @property
    def gearOutDegrees(self) -> float:
        '''Output gear's position in degrees.'''
        return float(self.mstepsToDegrees(self._msteps) / self._gearRatio)
    
    def _step(self):
        self._msteps = (self._msteps + self._dir) % (self.STEPS_PER_REV * self._mstepMode * self._gearRatio)

    def updateState(self, board: dict[int, bool]):
        '''A dumb way to get the motor to "listen" to state from sim_GPIO'''
        self._dir = -1 if board[self.PINS["dir"]] else 1

        if not board[self.PINS["step"]]:  # Resets has _hasMoved on LOW
            self._hasMoved = False
        if not self._hasMoved and board[self.PINS["step"]]:  # steps if "powered" by pin once per HIGH
            self._step()
            self._hasMoved = True

        if ((ms1 := board.get(self.PINS["ms1"])) is not None
                and (ms2 := board.get(self.PINS["ms2"])) is not None
                and (newMode := MSTEP_PIN_STATES[(ms1, ms2)]) != self._mstepMode):
            # recalibrate to new mode resolution
            self._msteps += _closestLoopMovement(self._msteps,
                                                 self._msteps + (newMode - (self._msteps % newMode)),
                                                 newMode)
            self._msteps = int((self._msteps * newMode) / self._mstepMode)  # convert to new mode units
            self._mstepMode = newMode

    def debugSettings(self):
        '''Displays vMotor settings'''
        print(self.name, "SETTINGS")
        print("Pins:", self.PINS)
        print("Direction:", "CC" if (self._dir < 0) else "CW")
        print("Steps per motor rev:", self.STEPS_PER_REV)
        print("Microstepping:", ("Off" if (self._mstepMode == 1) else ("1/" + str(self._mstepMode))))
        if self._mstepMode != 1:
            print("Microsteps per motor rev:", self.STEPS_PER_REV * self._mstepMode)
        print("Steps per gear rev:", self.STEPS_PER_REV * self._gearRatio)
        if self._mstepMode != 1:
            print("Microsteps per gear rev:", self.STEPS_PER_REV * self._mstepMode * self._gearRatio)
        print("Gear ratio:", self._gearRatio)
        print()

    def debugStatus(self):
        '''Displays vMotor and gear position in (micro)steps and degrees'''
        print(self.name, "STATUS")
        print("Direction:", "CC" if (self._dir < 0) else "CW")
        stepLabel = "Step" if (self._mstepMode == 1) else f"Microstep (1/{self._mstepMode})"
        print(stepLabel, "motor position:", self.steps % self.STEPS_PER_REV, "of", self.STEPS_PER_REV * self._mstepMode)
        print(stepLabel, "gear position:", self.steps % self.STEPS_PER_REV, "of", self.STEPS_PER_REV * self._mstepMode * self._gearRatio)
        print("Motor degree position:", self.degrees)
        print("Output gear degree position:", self.gearOutDegrees)
        print()
