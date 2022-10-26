'''Simulates RPi.GPIO output states using GPIO.output(channel(s), value(s)) for sim_motor

It's basically a glorified dictionary for output pin states intended for testing purposes.

You can use pin or GPIO BCM numbers. This module doesn't differentiate.

based on
https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/
https://sourceforge.net/p/raspberry-gpio-python/code/ci/default/tree/source/py_gpio.c#l331
'''
from datetime import datetime
import json  # load
import sys  # argv, exit

import sim_motor


VERBOSE = True
ULTRA_VERBOSE = False

def timestamp(): return datetime.now().strftime('%H:%M:%S.%f')

def vprint(*args): print(f"[{timestamp()}]:", *args)


#########################################
########## Simulated Constants ##########
#########################################

BOARD = "GPIO.BOARD"  # dummy only for sim output
BCM = "GPIO.BCM"  # dummy only for sim output
IN = "in"  # dummy not simulated/should raise Exception
OUT = "out"
HIGH = True
LOW = False

# dummy info
RPI_INFO = {"P1_REVISION": "This is a simulation! We're all living in a simulation! AAAAAAAAAH-"}
VERSION = "Version: sim_GPIO v'HopefullyWorking'"

#########################################

#########################################
########## Simulated "Board" ############
#########################################

_mode = None  # BOARD or BCM
_ioModes: dict[int, str] = {}
_board: dict[int, bool] = {}  # channel: (io_mode, state)
_pinToMotor: dict[int, list[sim_motor.vMotor]] = {}  # channel: (vMotors, ...)

#########################################


# Module initialization
CONFIG_FILE = "track-config.json"
PIN_JSON_PATHS = ("AltConf/AltDirGPIO", "AltConf/AltStepGPIO",
                  "AziConf/AziDirGPIO", "AziConf/AziStepGPIO",
                  "ms1pin", "ms2pin")

def _getJsonData(dJson, path):
    '''recursively gets JSON data given deserialized JSON and a path'''

    if not (pSplit := path.partition("/"))[1]:
        return dJson[pSplit[0]]

    return _getJsonData(dJson[pSplit[0]], pSplit[2])

# initialize board with pins from track-config.json
try:
    with open(CONFIG_FILE) as config:
        trackConfig = json.load(config)
except OSError:
    print("Error: track-config.json could not be open. Does it exist?")
    sys.exit()

for path in PIN_JSON_PATHS:
    try:
        pin = _getJsonData(trackConfig, path)
        _board[pin] = LOW
        _ioModes[pin] = None
        _pinToMotor[pin] = []
        if VERBOSE:
            vprint(f"Initializing pin {pin} from {CONFIG_FILE}/{path} with LOW")
    except KeyError:
        print(f"JSON path '{path}' could not be resolved and was skipped.")


def _plugIn(motor: sim_motor.vMotor, channel: int):
    if motor not in (mlist := _pinToMotor[channel]):
        mlist.append(motor)
        if VERBOSE:
            print(f"Plugging in {motor.name} into channel", channel)
    elif VERBOSE:
        print(f"You already plugged {motor.name} into channel", channel)

def _setIoMode(channel: int, ioMode: str):
    if ioMode == IN:
        raise Exception("Error: Input pins are not simulated in this module!")
    _ioModes[channel] = ioMode
    if VERBOSE:
        vprint(f"Setting pin {channel} to {ioMode} mode")

def _setState(channel: int, state: bool):
    ioMode = _ioModes[channel]
    if ioMode is None:
        raise Exception(f"Error: ioMode for pin {channel} is not set")
    elif ioMode == IN:
        raise Exception("Error: Input pins are not simulated in this module!")
    _board[channel] = state
    if ULTRA_VERBOSE:
        vprint(f"Setting pin {channel} ({ioMode}) to {'HIGH' if state else 'LOW'}")

    motors = _pinToMotor.get(channel)
    for motor in (motors if motors is not None else ()):
        motor.updateState(_board)

def _freeChannel(channel: int):
    _board[channel] = False
    _ioModes[channel] = None
    if VERBOSE:
        vprint(f"Freeing pin {channel}")

# Utility fuctions
def vPlugIn(motor: sim_motor.vMotor, channel: int | list[int] | tuple[int]):
    '''"Plug" your vMotor into a board pin. This needs to be done for the vMotor to work'''
    try:
        if isinstance(channel, (list, tuple)):
            for c in channel:
                _plugIn(motor, c)
        elif isinstance(channel, int):
            _plugIn(motor, c)
        else:
            raise ValueError("Error: channel should be int or list/tuple of ints")
    except KeyError as exc:
        raise KeyError(f"Error: One of the given channel(s) {channel} does not exist.") from exc


def printBoard():
    '''Prints the board's state'''
    print(f"Board state [{timestamp()}]:")
    print("Mode:", _mode)
    for channel, state in _board.items():
        print(f"{channel} ({_ioModes[channel]}): {'HIGH' if state else 'LOW'}")
    print()


#########################################
########## Simulated Functions ##########
#########################################

def getmode() -> str:
    '''Dummy getter: gets stored value (BOARD or BCM), but mode NOT simulated

    I don't know what kind of value this is supposed to return
    so you get a string.
    '''
    return _mode

def setmode(mode: str):
    '''Dummy getter: will store value (BOARD or BCM), but mode NOT simulated'''
    global _mode
    if VERBOSE:
        vprint("Setting channel mode (Not simulated) to", mode)
    _mode = mode

def setwarnings(isSet: bool):
    '''Dummy function: no effect, NOT simulated'''
    if VERBOSE:
        vprint("Set warning mode (Not simulated) to", isSet)

def setup(channel: int | list[int] | tuple[int], ioMode: str | list[str] | tuple[str]):
    '''Sets a channel's io mode
    
    Note: Since this module only simulates output it will raise an
    exception when setting a channel to IN mode
    '''
    try:
        if (isinstance(channel, (list, tuple)) and isinstance(ioMode, (list, tuple, str))):
            if isinstance(ioMode, str):
                ioMode = [ioMode] * len(channel)
            if len(channel) != len(ioMode):
                raise ValueError("Error: channel and ioMode must be the same length or ioMode must be single value")

            for c, io in zip(channel, ioMode):
                _setIoMode(c, io)

        elif isinstance(channel, int) and isinstance(ioMode, str):
            _setIoMode(channel, ioMode)

        else:
            raise ValueError("Error: channel and ioMode much be matching int-str pair(s) in single value, list, or tuple")
    except KeyError as exc:
        raise KeyError(f"Error: One of the given channel(s) {channel} does not exist.") from exc

def output(channel: int | list[int] | tuple[int], state: bool | list[bool] | tuple[bool]):
    '''Sets a channel's state by pin or GPIO BCM number

    Note: This function may not simulate all checks for valid arguments
    '''
    try:
        if (isinstance(channel, (list, tuple)) and isinstance(state, (list, tuple, bool))):
            if isinstance(state, bool):
                state = [state] * len(channel)
            if len(channel) != len(state):
                raise ValueError("Error: channel and state must be the same length or state must be single value")

            for c, s in zip(channel, state):
                _setState(c, s)

        elif isinstance(channel, int) and isinstance(state, bool):
            _setState(channel, state)

        else:
            raise ValueError("Error: channel and state much be matching int-bool pair(s) in single value, list, or tuple")
    except KeyError as exc:
        raise KeyError(f"Error: One of the given channel(s) {channel} does not exist.") from exc

def cleanup(channel: int | list[int] | tuple[int] | None = None):
    '''"Frees" channels by setting state to LOW and ioMode to None

    Note: Should not raise exception if channel does not exist/already been freed'''
    try:
        if channel is None:
            channel = tuple(_board.keys())

        if (isinstance(channel, (list, tuple))):
            for c in channel:
                _freeChannel(c)
        elif isinstance(channel, int):
            _freeChannel(channel)
        else:
            print("Warning: cleanup() canceled because of invalid input")
            print(channel)
    except KeyError:
        print(f"Warning: One of the given channel(s) {channel} may not exist and has been skipped in cleanup().")

#########################################
