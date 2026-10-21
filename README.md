# Quadcopter Control Lab

**English** | [繁體中文](README.zh-TW.md)

**▶ Try it online: https://adevlog.github.io/drone-sim/**

A browser-based quadcopter simulator for understanding how PID gains and sensors affect flight. Every signal in the chain — command → cascaded PID → mixer → motors → airframe → sensors → feedback — is visible and adjustable, and you see the aircraft respond immediately. Single HTML file, nothing to install. (The interface is in Traditional Chinese.)

## What you can do

| Mode | Contents |
|---|---|
| Single-axis test rig (Roll / Pitch / Yaw / Throttle) | Other axes locked; one channel's cascaded PID with square, step and sine commands; rise time, overshoot, settling time, steady-state error |
| 3-axis attitude | All three axes at once, cross-coupling, altitude hold and tilt compensation; primary flight display (PFD) |
| Free flight | PX4 flight modes Acro / Stabilized / Altitude / Position; stick arming, crash detection, flight trail |
| Exam practice | Taiwan CAA professional basic-class multirotor test field (AC107-005D fig. 9); pilot's-eye view, 5-second hover timer, tolerance band and altitude cues |
| Hover tuning | Starts hovering at 2 m with the camera locked on the aircraft; origin marker, target point and drift line; hover metrics (drift, tilt, rate jitter, PWM jitter) |

- Click any block in the signal diagram to see its formula with the current live values substituted.
- Parameters use PX4 names (`MC_ROLLRATE_P`, `MPC_XY_VEL_P_ACC`, …); two handling profiles: PX4 default and consumer-style.
- **Motors & sensors panel** (3-axis, free flight, hover tuning): per-motor efficiency (PX4 numbering), gyro noise / bias / low-pass cutoff, accelerometer noise / bias, and attitude estimation using the gyro, the accelerometer, or both (simplified Kalman filter), with a true-vs-estimated angle chart.
- Things to try: weaken one motor and set the rate I gains to 0 → the drone settles at a fixed tilt and drifts away; lower rate P → visible wobble; raise D with gyro noise → motor output jitter; gyro-only estimation with a gyro bias → integration drift.

## Gesture Flight (experimental)

**▶ https://adevlog.github.io/drone-sim/gesture/**

Fly with your hand: an AI hand-tracking model (MediaPipe, running locally in the browser) follows your fingertips through the webcam, and you swipe a virtual ball whose spin commands the drone (altitude hold, Position mode). Needs a camera and HTTPS (the online version works). Details and design rationale: [gesture/REPORT.md](gesture/REPORT.md).

## Controls (Mode 2)

| Action | Keyboard | Xbox controller / on-screen sticks |
|---|---|---|
| Throttle | W / S | Left stick up/down |
| Yaw | A / D | Left stick left/right |
| Pitch | ↑ / ↓ | Right stick up/down |
| Roll | ← / → | Right stick left/right |
| Arm | Hold S + D for about 1 s | Hold left stick bottom-right for about 1 s |
| Disarm | After landing, hold S + A for about 1 s | Hold left stick bottom-left for about 1 s |
| Fullscreen / Re-fly | F / R | Buttons at the top right of the 3D view |

Gamepads are only readable on HTTPS pages or local files (the online version works).

## Run locally

Download `index.html` and open it in Chrome, Edge or Firefox. three.js is loaded from cdnjs, so an internet connection is needed.

## Docs and tests

- [ARCHITECTURE.md](ARCHITECTURE.md) (Traditional Chinese): program structure, module map, event table, design rationale for the physics, controllers and sensors, and how to add or remove a feature.
- [gesture/REPORT.md](gesture/REPORT.md): Gesture Flight technical report (model, coordinate mapping, mirror detection, hand selection, known issues).
- [tests/](tests/): core computation tests (node) and browser regression tests (playwright); run `tests/run_all.sh`.

## Disclaimer

For teaching control principles only. Physical parameters are estimates for a typical 1.5 kg quadcopter, and the consumer handling values were chosen for exam practice. **They are not measured data from any specific aircraft** and do not replace real flight training or the official test rules. Magnetometer, barometer and GPS are currently assumed perfect.

## License

[MIT License](LICENSE) © 2026 [AdevLog](https://github.com/AdevLog)
Free to use, modify and distribute; please keep the copyright notice and the license text.
