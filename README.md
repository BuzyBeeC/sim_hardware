# sim_hardware

A package containing simulated hardware for developing and testing https://github.com/BuzyBeeC/Open-Star-Tracker

As of right now, `sim_motor` is **obsolete** and no longer maintained. It has served its purpose for now (mostly to ensure that `sim_GPIO` works as intended). The `MotorController` class from the `motor_control` module in the [main repository](https://github.com/BuzyBeeC/Open-Star-Tracker) has superseded the `vMotor` class for testing (and production) purposes, with slightly different functionality.

`sim_GPIO` continues to be useful as a drop-in simulation for `RPi.GPIO` when developing without a real Raspberry Pi board that the latter requires.