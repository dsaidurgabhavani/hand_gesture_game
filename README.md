# 🎮 Hand Gesture Runner (100% Hands-Free)

An endless runner game controlled **completely through webcam hand gestures**. 
**No keyboard, mouse, or external input device is needed at ANY point!**

---

## 🌟 Key Features

- **100% Zero-Touch Hands-Free Operation:**
  - **Start Game:** Simply show your hand ✋ to the camera. It detects your hand instantly, fills a smooth 0.8s confirmation ring, and begins a 3-2-1 countdown!
  - **Steer:** Move your hand Left, Center, or Right across the camera frame. Features intelligent **hysteresis deadzones** and exponential smoothing to eliminate lane-switching jitter.
  - **Jump:** Show **Thumbs-Up 👍** OR simply **raise your hand high** (`palm_y < 0.28`). The character leaps in a smooth parabolic arc with dynamic ground shadow scaling.
  - **Slide:** Make a **Closed Fist ✊** OR **lower your hand** (`palm_y > 0.74`). Slides under yellow aerial laser beams with ground spark particles.
  - **Auto-Pause:** Step away or take your hand off camera, and the game automatically pauses! Return your hand to resume with a smooth countdown.
  - **Play Again:** On Game Over, simply show your hand ✋ to restart instantly!
- **Single Unified Window with Live Picture-in-Picture (PiP) HUD:**
  - Real-time mirrored webcam feed embedded directly inside the top-right corner.
  - Cyberpunk neon hand skeleton tracking and lane zones (Left | Center | Right) with live gesture badges.
- **Synthesized Real-Time Audio (Zero Missing Files):**
  - Stereo retro-arcade audio synthesized on-the-fly via NumPy: jump whooshes, slide swooshes, coin chime harmonics, crash impacts, and countdown blips.
- **Power-Ups & Collectibles:**
  - 🪙 **Gold Coins:** Collect for +25 points and build your high score.
  - 🛡️ **Energy Shield:** Blue forcefield that absorbs 1 obstacle collision.
  - 🧲 **Coin Magnet:** Pulls nearby coins directly to your runner for 9 seconds.
- **Safe Runway on Start:**
  - 3.2 seconds of obstacle-free runway when the run begins so you can get comfortable before hurdles appear.
- **Persistent High Scores:**
  - Automatically saves and loads your personal best score in `highscore.json`.

---

## 🖐️ Gesture Reference Guide

| Action | Hand Gesture | Description |
| :--- | :--- | :--- |
| **Steer Left / Right** | Move Hand Across Camera | Move hand to Left, Center, or Right zone. Smooth easing prevents jitter. |
| **Jump** | 👍 **Thumbs-Up** or **Raise Hand High** | Parabolic leap over red hurdles. |
| **Slide / Duck** | ✊ **Closed Fist** or **Lower Hand** | Duck and slide under yellow aerial beams. |
| **Start / Play Again** | ✋ **Show Hand to Camera** | Detects hand and launches the countdown smoothly. |
| **Auto-Pause** | ❌ **Remove Hand** | Taking hand off camera pauses automatically. Put hand back to resume. |

---

## 🚀 How to Run

### Option 1: One-Click Launcher (Windows)
Double-click [**`run_game.bat`**](file:///c:/Users/sunil/Downloads/Hand_Gesture_Runner/run_game.bat) in File Explorer.

### Option 2: From Terminal / VS Code
```powershell
python main.py
```
