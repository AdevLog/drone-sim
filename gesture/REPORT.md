# Gesture Flight — Technical Report

**English** | [繁體中文](REPORT.zh-TW.md)

**▶ Try it online: https://adevlog.github.io/drone-sim/gesture/**

> An extension of the Quadcopter Control Lab (drone-sim): swipe a virtual ball with your hand, tracked by an AI hand-landmark model, to fly the simulated drone.
> Final report for a programming course. Author: AdevLog. (The app interface is in Traditional Chinese.)

| File | Contents |
|---|---|
| `index.html` | Landing page: how to fly and camera notes |
| `drone-gesture-cam.html` | The app: altitude-hold flight (Position mode) + camera hand gestures; mouse / touch swiping also works |
| `REPORT.md` / `REPORT.zh-TW.md` | This report (English / Traditional Chinese) |

Single HTML file; the only dependencies are CDNs (three.js r128, MediaPipe Tasks Vision). The camera requires **HTTPS or localhost**: opening a downloaded file directly on a phone reports "permission denied".

---

## 1. Goal

- The course grades on **AI**: put a neural-network hand tracker inside a flight-control loop.
- Reuse the Lab's physics and controllers (SIM-CORE), taking only what is needed; the Lab's `index.html` is untouched.
- Concept: a **virtual ball** sits at the bottom right; its rotation is the drone's command. Your hand (or the mouse) swipes the ball, and **when you stop, the ball keeps spinning on its own momentum**.

## 2. How the idea evolved (why a virtual ball)

| Stage | Idea | Verdict |
|---|---|---|
| 1 | Microphone → speech-to-text → LLM → command | Works, but 1–3 s latency suits only high-level commands; an API key can't live in a public HTML file |
| 2 | Gesture → fixed command (fist = hover…) | Simple, but discrete triggers, not continuous control |
| 3 | Hand position / tilt → sticks | A single camera reliably measures only 2 in-plane axes; tilting toward the camera needs depth and is noisy |
| 4 | **Virtual ball**: a swipe adds angular velocity; the ball's rotation is the command | Adopted. Swiping is a continuous command, momentum handles "let go", and the ball's three axes map onto three control axes |

- A quadcopter has 6 degrees of freedom but only 4 control inputs (underactuated): roll / pitch / yaw / thrust. Altitude is held for now, so the ball's 3 axes are enough.
- Most existing gesture-drone projects classify a gesture into a command (kinivi/tello-gesture-control, AirSim examples); continuous control usually uses a Leap Motion or an IMU glove.
- Related work: dragging a sphere in 2D to rotate a 3D object (Chen 1988 Virtual Sphere, Shoemake 1992 ArcBall) is **position control**; trackballs are also used for robot teleoperation (Ng, Mahony & Lau 2019, cable-driven parallel robots). This project is **rate control** (ball angular velocity = velocity command, with momentum), driven by fingertips seen through an ordinary webcam. I found no identical combination (a quick search, not a systematic literature review).

## 3. Architecture

```
mouse / touch ─┐
               ├─► virtual ball (angular velocity ω, momentum) ─► sticks ─► Position controller ─► physics ─► 3D view
camera ─► MediaPipe (palm detection → 21 landmarks → gesture class) ─► pick hand ─► mapping ─► fingertip swipe ─┘
```

- Ball ω → velocity command: roll forward/back = forward speed, roll left/right = sideways speed, spin = yaw rate.
- Controller: Position mode + 2 m altitude hold (velocity PID → tilt → cascaded attitude PID → mixer).
- Ball stopped = sticks centered = brake and hold position.
- From SIM-CORE: 1 kHz physics, 250 Hz control, PX4 Quad X motor numbering, first-order motor lag, quaternion attitude, linear drag. Sensor errors, Kalman filter, arming, other flight modes and teaching panels are removed.

Coordinate chain (hand to motors):

```
camera pixels ─(mirror check χ)→ user's view
camera 3D (x right, y down, z away) ─(180° about vertical)→ user frame W (X right, Y up, Z toward user)
fingertip motion in W ─(hand size as the ruler)→ contact point and motion on the on-screen ball
contact r × Δp → ball angular velocity ω (top view: x right, y nose, z up)
ω → sticks → heading-frame velocity command ─(rotate by heading ψ)→ NED velocity command
→ acceleration → thrust vector → tilt → cascaded attitude PID → mixer → motors
```

## 4. Virtual ball

### 4.1 Formula

The ball is drawn **from above**: screen x = right (body right), y = up (nose), z = toward the viewer (body up). A swipe Δp at contact point r (on the unit sphere):

```
Δω = GAIN · (r × Δp)
```

- Swipe the center (r ≈ (0,0,1)) → only x, y components → roll forward/back, left/right.
- Swipe tangentially along the rim (r on the equator) → only z → spin (yaw).
- Sign convention: rolling forward (negative about x) = fly forward, rolling right (positive about y) = move right, clockwise spin seen from above (negative z) = turn right.

### 4.2 Feel

| Parameter | Value | Note |
|---|---|---|
| GAIN | 1.3 | Raised from 1.0 so the ball is easier to swipe |
| Max rate | 4 rad/s ↔ 3 m/s; 2 rad/s ↔ 90°/s | |
| Damping while swiping | none (swipes only add speed) | "ball follows hand speed" made a decelerating hand slow the ball down |
| Friction after release | 0.01 /s horizontal, 1.5 /s spin | **No friction in camera mode**; a fist stops it |
| Instant stop | double-click, press and hold, Space, fist | |

### 4.3 Active zone

A light-colored **zone** surrounds the ball. In camera mode, the hand swipes only while the palm center is inside it; moving out = letting go, and the ball coasts. This is how you release the ball without making a fist.

## 5. Camera hand gestures

### 5.1 Model architecture and weights

Google's **MediaPipe Gesture Recognizer** (`gesture_recognizer.task`, **float16**, pretrained, no training needed), running locally in the browser via WebAssembly; video is never uploaded. Three networks in a pipeline:

| Stage | Architecture | Input → output |
|---|---|---|
| ① Palm detection, BlazePalm | Single-shot detector (BlazeFace-like), encoder-decoder (FPN-like), focal loss, square anchors only | Full image → palm boxes |
| ② Hand landmarks | Shared feature extractor, three heads | Hand crop → 21 points (image coords + 3D metric world coords) + presence score + handedness |
| ③ Gesture classifier | Embedding: fully connected net with residual blocks → 128-D; classifier: fully connected → 8 classes | Landmarks + handedness → gesture |

- It detects palms rather than whole hands: a palm is close to rigid, so boxes are easy to estimate, and overlapping hands separate better under NMS.
- In video mode the next box comes from the previous frame's landmarks (tracking); palm detection reruns only when tracking is lost (or fewer hands than `numHands` are tracked). The whole pipeline takes about 16.8 ms on a Pixel 6 CPU.
- Landmark training data: ~6K real images, 10K gesture images, 100K synthetic hands; **depth labels come only from synthetic data**, so single-camera depth is an estimate.
- Seven built-in static gestures; dynamic gestures are officially unsupported. This project uses only **Closed_Fist** (stop); swiping is computed entirely from landmarks.

Division of labor: **the neural networks answer "where is the hand and what gesture is it"; this project's code answers "how does the hand move → how does the ball turn".**

### 5.2 Coordinates and mirror detection (where most bugs were)

**Frames:** the user sits facing the screen and the camera faces the user. Camera frame (x right, y down, z increasing away from the camera) → user frame W (X = user's right, Y = up, Z = toward the user): facing each other, they differ by a **pure 180° rotation about the vertical axis** (determinant +1). A right hand stays a right hand.

| View (right hand raised, palm toward camera) | You see | Thumb on | Which hand |
|---|---|---|---|
| Raw camera image | palm | right | right (rotated 180°) |
| Mirror / selfie view | palm | left | **left** (reflected) |
| The user's own eyes (the goal) | back of hand | left | right |

Flipping only X is a **reflection** (determinant −1): it turns a right hand into a left hand, the person in the mirror. The 2D positions match "the user's eyes", but depth is reversed, and so is the direction of every rotation (axial vector).

**Mirror detection (chirality triple product):** laptop cameras often mirror the image in the driver, so the app must detect it.

```
χ = −(thumb base − wrist) · [(pinky base − wrist) × (index base − wrist)]      (in camera coordinates)
```

- The bracket is a right hand's back-of-hand normal (pointing from palm to back); the thumb base sits on the palm side, so a real right hand gives χ > 0.
- A triple product is the sign of a determinant: **unchanged by rotation, flipped by reflection**. χ > 0 = a right hand was reconstructed = input not mirrored; χ < 0 = input mirrored.
- With the thumb flat against the palm, χ ≈ 0 is unreliable, so only frames with |χ| ≥ 0.15 vote, and the decision is smoothed.

```
not mirrored: W = (−x, −y, z)
mirrored:     W = ( x, −y, z)   (the reconstructed hand's x is already flipped once)
2D display always shows "what the user's eyes see": flip unmirrored input, keep mirrored input
```

> The earlier version inferred mirroring from MediaPipe's Right/Left label (the docs say it assumes selfie-mirrored input). In practice, with tasks-vision, the result was reversed: the virtual hand became the mirror-image left hand, and the user had to press two "invert" buttons to compensate. Inferring geometry from a model's label is fragile, so the app now checks the geometry directly.

### 5.3 Mapping: the hand's size is the ruler

| Problem | Cause |
|---|---|
| The ball is at the bottom right, so the hand had to reach the camera's bottom-right corner | camera coordinates were scaled straight onto the screen |
| The farther the hand, the smaller the virtual hand and the weaker the swipe | size and motion were measured in pixels |

**Scale:** each frame, a least-squares fit of the 2D landmarks against the 3D world landmarks (x, y) gives s = camera pixels per meter (weak-perspective scale). It depends only on distance, not on hand tilt (a 2D palm length shrinks with foreshortening). s is low-passed (0.15) so scale jitter doesn't read as motion.

```
screen position = ball center + (camera pixel − camera center) / s × (screen pixels per meter)
screen pixels per meter = 0.9 × ball radius / 0.09 m      (wrist → middle-finger base ≈ 9 cm drawn as 0.9 ball radii)
```

- Hand in front of the camera's center = virtual hand on the ball, at the same size near or far.
- Swipe distances use the same ruler, so the feel doesn't change with distance.

### 5.4 Swiping and yaw

The 5 fingertips act like 5 mouse cursors pushing the ball's surface, with the same rule as the mouse. Only their 2D image positions are used, not the estimated depth. Hand motion is split into two parts, with the pivot at the wrist:

```
phi = how much the fingertip-to-wrist vectors rotated (2D rigid rotation angle)
t   = fingertip centroid motion − the motion caused by rotating phi about the wrist
```

Using the centroid alone would read a twist as a translation (the pivot is the wrist, so the centroid moves on an arc).

**Yaw (avoiding accidental turns while swiping):** previously any swipe along the rim turned the drone, and fingers naturally arc while swiping. Now a twist counts as yaw only when both hold:

1. **Posture gate:** the palm-plane normal (wrist, index base, pinky base: rigid, steadier than fingertips) is within 30° of Z, i.e. the palm stands up facing the screen (palm or back toward the camera); it exits above 40° (hysteresis). A palm parallel to the ground shows the camera only its edge, with landmarks occluding each other.
2. **Dominant-motion lock:** in one push, the twist arc |phi| × fingertip-to-wrist distance must be ≥ 2 × the translation to count as yaw (and that push doesn't translate); otherwise only the translation counts and the incidental twist is discarded.

The direction is like a steering wheel facing you: counter-clockwise = turn left.

**Jitter suppression:**

| Mechanism | How | Why |
|---|---|---|
| Low-pass | fingertip EMA 0.5 | smoothing |
| **Anchor method** | push the ball only when the hand has moved > 0.06 ball radii or twisted > 5° from the anchor, then move the anchor | a per-frame dead zone lets jitter accumulate (119° in 10 s with a still hand); with an anchor, jitter only wobbles around it |
| Arc threshold | a twist also needs angle × fingertip-to-wrist distance to be long enough | close-together fingers make the angle noisy |
| Settling | wait 6 frames after entering the zone, opening a fist, a tracking jump, or switching hands | the hand shape is still changing |
| Glitch drop | discard jumps > 0.9 ball radii or 45° | tracking errors |

### 5.5 Multiple people: use only the nearest, largest hand

**Problem:** with `numHands: 1` the model picks a hand by **confidence**, not size. If the user's hand briefly leaves the frame, re-detection may lock onto a small hand in the crowd behind and keep tracking it. Ignoring it in app code doesn't help: the model only knows "I'm already tracking 1 hand, I'm full" and won't look for the user's hand. MediaPipe has no "pick by size" option and no "drop this hand" API.

**Size gate:** hands whose palm length (wrist → middle-finger base, ~9 cm) is < 12% of the frame height are ignored, and the app shows "hand too far". Physical meaning (pinhole camera):

```
palm fraction of frame r = L / (2 · Z · tan(VFOV/2))   →   Z = L / (2 · r · tan(VFOV/2))
typical laptop camera (≈60° horizontal FOV, 4:3, tan(VFOV/2) ≈ 0.43): Z ≈ 0.09 / (2 × 0.12 × 0.43) ≈ 0.87 m
```

- So hands farther than about 87 cm don't count; at that distance the frame height spans 75 cm of real space.
- It also caps **jitter**: the virtual hand's screen scale is fixed, so on-screen jitter ∝ meters per camera pixel. At the threshold, 480p gives about 1.6 mm per pixel, with the palm about 58 pixels long.
- A ratio rather than a distance: a distance needs the camera's field of view (device-specific, unreadable by the page); the ratio maps directly to how many pixels the hand has, i.e. tracking quality.

**Two recognizers:** both are loaded, and each frame feeds only one (inference cost doesn't double; only memory does).

| Mode | Fed each frame | Switch when |
|---|---|---|
| 1 (normal) | R1 (`numHands: 1`) | the tracked hand is too small → mode 2 |
| 2 (interference) | R2 (`numHands: 2`), pick the largest hand above the gate | only one large-enough hand for 0.5 s (or no hand) → mode 1 |

- When returning to mode 1 the small hand is gone: R1's stale box finds nothing → re-detection → it finds the user's hand.
- `setOptions` is not used to change `numHands`: it rebuilds the model's processing graph (a hitch, tracking state lost), and switching back might grab the small hand again and loop.
- **Stickiness:** the hand whose wrist is nearest last frame's is the same hand (return order isn't fixed); another hand must be 1.3× larger to take over, and switching hands resets the scale and the swipe anchor.

### 5.6 Display

- **3D virtual hand:** viewed in perspective from behind the user's hand, 25° to the right and 15° above; near bones thick and dark, far ones thin and faint; the palm is colored by the back-of-hand normal and labeled "back / palm".
- **Five-finger plane panel** (top left, under the status box):
  - Newell's method over thumb → pinky gives the fingertip-plane normal (gray line; for a right hand it points from back to palm).
  - Black bar = torque actually applied to the ball.
  - Title line: state, fps, mode 1/2, number of hands, palm %, inference ms, yaw allowed (palm angle), χ, raw MediaPipe label, mirror decision.
- Hand 3D rotation (display only): 5 fingertips as a rigid body, least squares `J · Δθ = Σ aᵢ × dᵢ` (J = the fingertips' inertia tensor).
- Three "invert" buttons (forward / sideways / yaw) for fixing signs during testing, saved in the browser; normally none is needed.

## 6. Bugs and fixes (for future maintainers)

| Symptom | Cause | Fix |
|---|---|---|
| Assumed the laptop camera gives the raw image | laptop cameras mirror in the driver | automatic detection |
| Calibrating mirroring by "move your hand right" got it backwards | the hand is already moving when it enters or pauses at the edge | handedness-based detection (no motion needed) |
| **Right hand shown as the mirror-image left hand, labeled "palm", thumb on the right; the user pressed two invert buttons to compensate** | MediaPipe's Right/Left convention is the opposite of the docs | chirality triple product χ, no labels; saved invert settings reset |
| Ball dragged down by the hand, never spins up | "ball follows hand speed" = damping | swipes only add speed |
| Ball slowly turns with a still hand | per-frame dead zone accumulates jitter | anchor method |
| Gesture direction opposite to the ball (several times) | driving the ball by the hand's 3D rotation, plus "flip" and "contact physics (−ωx, −ωy, +ωz)", both of which are **reflections** | fingertip contact (mouse semantics) + pure-rotation frames |
| Twisting also moved sideways | fingertip centroid used as the pivot | pivot at the wrist |
| **Hand had to reach the camera's bottom-right corner; tracking poor at the edge** | camera coordinates scaled straight onto the screen | hand size as the ruler, camera center = ball center |
| **Swipes often triggered yaw** | any rim swipe turned the drone; fingers arc while swiping | palm-facing-screen gate + dominant-motion lock |
| **Hands in the crowd behind took over** | the model picks by confidence and holds on | size gate + R1/R2 switch picking the largest hand |
| "Permission denied" on a phone opening the downloaded HTML | the camera is HTTPS/localhost only; in-app HTML viewers (WebView) usually don't grant it | host on GitHub Pages |

## 7. Verification

This development environment can't reach the CDNs, so the 3D view and the real MediaPipe were tested by the user in a browser.

1. **Core in node (CORE block):** simulated swipes → drone response. E.g. a forward swipe of one diameter cruises at about 1.1–1.75 m/s while altitude stays at 2.00 m.
2. **Headless Chromium + three.js stub:** mouse / touch events → page state, no errors.
3. **Synthetic hand** (a full 21-point right hand), with mirrored and unmirrored input:
   - Chirality χ: +0.38 unmirrored, −0.38 mirrored; both restore to thumb on the user's left, back of hand toward the user.
   - Hand picking: user only → mode 1; R1 tracking a small hand → ignored, switch to mode 2; R2 seeing both (either return order) → the user's hand is chosen; user alone for 0.6 s → back to mode 1.
4. **User test on real hardware** (laptop camera): right hand shown as the back of the hand, thumb on the left; moving right moves the virtual hand right; forward, sideways and yaw directions correct with no invert buttons pressed.

## 8. Done

- [x] Altitude-hold flight: mouse / touch swiping, start flag and 10 m markers, fading trail, re-fly (R), fullscreen (F)
- [x] MediaPipe loading with version fallback and GPU → CPU fallback
- [x] Mirror detection by chirality χ; pure-rotation frames
- [x] Hand-size mapping (camera center = ball center, fixed virtual hand size)
- [x] Fingertip swiping (translation + twist about the wrist), anchor-based jitter suppression, fist to stop, active zone
- [x] Yaw: palm-facing-screen gate + dominant-motion lock
- [x] Multiple people: size gate, R1/R2 recognizers, stickiness
- [x] 3D virtual hand (back / palm), five-finger plane panel with debug info
- [x] Live on GitHub Pages, landing page

## 9. To do

1. **Phone test:** open on GitHub Pages, landscape on a stand, front camera; check fps, inference ms and GPU / CPU fallback.
2. **Tuning:** adjust `HAND.MIN_R` (size gate), `PALM_R` (virtual hand size), `DOM` (dominance ratio), `SCALE_EMA` (position drift when the hand moves quickly toward/away from the camera).
3. **Stickiness:** two hands close together on screen (wrists < 15% of frame width apart) may be confused; if seen in testing, also compare sizes.
4. **(Bonus) Train a model:** a custom gesture with MediaPipe Model Maker, compared against the rule-based approach.
5. **(Optional) Performance:** if inference ms is high, switch to HandLandmarker (fist by geometry) or a Web Worker.

## 10. Kept but unused (annotated per project convention, not deleted)

- `HAND.FACE` (removed): flipping the skeleton in place, proven to be a reflection.
- `MAP_GAIN` (removed): old mapping "camera center region × 1.4 onto the full screen", replaced by §5.3.
- MediaPipe Right/Left label: no longer used for decisions; shown in the title line for comparison.
- `HAND.CONTACT = [−1, −1, 1]`, `HAND.GAIN`, `handRotation()`: the old "drive the ball by the hand's 3D rotation"; `handRotation()` is now display-only.

## References

- [Gesture recognition task guide — Google AI Edge](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer)
- [Gesture recognition guide for Web](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer/web_js)
- [Model card: Hand Gesture Classification](https://storage.googleapis.com/mediapipe-assets/gesture_recognizer/model_card_hand_gesture_classification_with_faireness_2022.pdf)
- [MediaPipe Hands: On-device Real-time Hand Tracking (arXiv 2006.10214)](https://arxiv.org/abs/2006.10214)
- [MediaPipe Hands docs (handedness assumes mirrored input)](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/hands.md)
- [Shoemake, ARCBALL (Graphics Interface 1992)](https://graphicsinterface.org/wp-content/uploads/gi1992-18.pdf)
- [A dual joystick-trackball interface for teleoperation (Ng, Mahony, Lau 2019)](https://researchportalplus.anu.edu.au/en/publications/a-dual-joystick-trackball-interface-for-accurate-and-time-efficie-2/)
- [kinivi/tello-gesture-control](https://github.com/kinivi/tello-gesture-control)
- [Flying the Crazyflie with Leap Motion — Bitcraze](https://www.bitcraze.io/2013/08/flying-the-crazyflie-with-leapmotion/)
