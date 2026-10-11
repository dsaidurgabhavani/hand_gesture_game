"""
Hand Gesture Runner - Pure Gesture-Controlled Endless Runner
=============================================================
A complete, 100% hands-free game controlled entirely via webcam hand gestures.
NO keyboard, mouse, or external input device is needed!

Controls:
- Steer: Move your hand Left / Center / Right across the camera view.
- Jump: Show Thumbs-Up 👍 OR raise your hand high.
- Slide: Make a Closed Fist ✊ OR lower your hand.
- Start / Play Again: Simply show your hand ✋ to the camera!
- Auto-Pause: Taking hand off camera pauses automatically; bring it back to resume!
"""

import os
import sys
import time
import json
import math
import random
import cv2
import pygame
import numpy as np
import mediapipe as mp

# -------------------------------------------------------------
# Configuration & Constants
# -------------------------------------------------------------
WIDTH, HEIGHT = 1080, 700
FPS = 60

# 3 Lanes with comfortable spacing
LANE_X = [WIDTH // 2 - 210, WIDTH // 2, WIDTH // 2 + 210]
PLAYER_Y = HEIGHT - 140

# Color Palette (Futuristic Neon / Arcade)
BG_DARK = (15, 18, 30)
ROAD_COLOR = (30, 34, 48)
ROAD_BORDER = (0, 235, 255)
ROAD_LINE = (65, 75, 105)
CYAN = (0, 240, 255)
GOLD = (255, 204, 0)
GOLD_LIGHT = (255, 245, 160)
RED_NEON = (255, 60, 90)
RED_GLOW = (255, 130, 150)
YELLOW_NEON = (255, 230, 40)
GREEN_NEON = (40, 255, 130)
PURPLE_NEON = (180, 70, 255)
BLUE_NEON = (60, 160, 255)
WHITE = (245, 248, 255)
GRAY = (140, 145, 165)
DARK_PANEL = (20, 24, 38, 220)

# Game States
STATE_READY = "READY"
STATE_COUNTDOWN = "COUNTDOWN"
STATE_PLAYING = "PLAYING"
STATE_PAUSED = "PAUSED"
STATE_GAMEOVER = "GAMEOVER"

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.json")


# -------------------------------------------------------------
# Real-Time Synthesized Sound System (No external audio files)
# -------------------------------------------------------------
class SoundFX:
    def __init__(self):
        self.enabled = False
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            self.enabled = True
            self.sounds = {
                "coin": self._synth_coin(),
                "jump": self._synth_jump(),
                "slide": self._synth_slide(),
                "crash": self._synth_crash(),
                "tick": self._synth_tick(),
                "go": self._synth_go(),
                "powerup": self._synth_powerup(),
                "shield_break": self._synth_shield_break(),
            }
        except Exception as e:
            print(f"[SoundFX] Audio initialization skipped: {e}")

    def _make_stereo(self, mono):
        mono = np.clip(mono, -32767, 32767).astype(np.int16)
        stereo = np.column_stack((mono, mono))
        return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))

    def _synth_coin(self):
        sr = 44100
        dur = 0.22
        t = np.linspace(0, dur, int(sr * dur), False)
        env = np.exp(-t * 16)
        wave1 = np.sin(2 * np.pi * 987.77 * t)
        wave2 = np.sin(2 * np.pi * 1318.51 * t) * 0.7
        audio = (wave1 + wave2) * env * 18000
        return self._make_stereo(audio)

    def _synth_jump(self):
        sr = 44100
        dur = 0.25
        t = np.linspace(0, dur, int(sr * dur), False)
        freq = np.linspace(220, 650, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / sr
        env = np.sin(np.pi * t / dur)
        audio = np.sin(phase) * env * 17000
        return self._make_stereo(audio)

    def _synth_slide(self):
        sr = 44100
        dur = 0.22
        t = np.linspace(0, dur, int(sr * dur), False)
        freq = np.linspace(350, 120, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / sr
        noise = (np.random.rand(len(t)) - 0.5) * 0.5
        env = np.sin(np.pi * t / dur)
        audio = (np.sin(phase) + noise) * env * 16000
        return self._make_stereo(audio)

    def _synth_crash(self):
        sr = 44100
        dur = 0.55
        t = np.linspace(0, dur, int(sr * dur), False)
        noise = (np.random.rand(len(t)) - 0.5) * 2.0
        low = np.sin(2 * np.pi * 75 * t)
        env = np.exp(-t * 7)
        audio = (noise * 0.85 + low * 0.5) * env * 24000
        return self._make_stereo(audio)

    def _synth_tick(self):
        sr = 44100
        dur = 0.08
        t = np.linspace(0, dur, int(sr * dur), False)
        env = np.exp(-t * 40)
        audio = np.sin(2 * np.pi * 587.33 * t) * env * 16000
        return self._make_stereo(audio)

    def _synth_go(self):
        sr = 44100
        dur = 0.35
        t = np.linspace(0, dur, int(sr * dur), False)
        env = np.exp(-t * 8)
        audio = (np.sin(2 * np.pi * 880 * t) + np.sin(2 * np.pi * 1760 * t) * 0.5) * env * 22000
        return self._make_stereo(audio)

    def _synth_powerup(self):
        sr = 44100
        dur = 0.32
        t = np.linspace(0, dur, int(sr * dur), False)
        freq = np.linspace(440, 1100, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / sr
        env = np.sin(np.pi * t / dur)
        audio = np.sin(phase) * env * 20000
        return self._make_stereo(audio)

    def _synth_shield_break(self):
        sr = 44100
        dur = 0.30
        t = np.linspace(0, dur, int(sr * dur), False)
        freq = np.linspace(700, 200, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / sr
        env = np.exp(-t * 10)
        audio = np.sin(phase) * env * 21000
        return self._make_stereo(audio)

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass


# -------------------------------------------------------------
# Hand Gesture Controller (Smooth Filtering & Hysteresis)
# -------------------------------------------------------------
class GestureController:
    def __init__(self, camera_idx=0):
        self.camera_idx = camera_idx
        self.cap = cv2.VideoCapture(camera_idx)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(1)
            if self.cap.isOpened():
                self.camera_idx = 1

        self.available = self.cap.isOpened()

        # MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Tracking state with Exponential Moving Average (EMA) smoothing
        self.hand_detected = False
        self.palm_x = 0.5
        self.palm_y = 0.5
        self.smooth_x = 0.5
        self.smooth_y = 0.5

        # Lane hysteresis state (prevents jitter between lanes)
        self.active_lane = 1  # 0: Left, 1: Center, 2: Right
        self.gesture = "NONE"
        self.last_seen_time = time.time()
        self.hud_surface = None

    def release(self):
        try:
            if self.cap and self.cap.isOpened():
                self.cap.release()
            self.hands.close()
        except Exception:
            pass

    def process(self):
        """Reads camera frame, runs MediaPipe, filters jitter, and updates gestures safely."""
        if not self.available:
            self.hand_detected = False
            self.gesture = "NO_CAMERA"
            return

        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.hand_detected = False
                self.gesture = "NO_FRAME"
                return

            # Mirror frame horizontally for intuitive interaction
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Run MediaPipe hand landmarker
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            self.hand_detected = False
            detected_gesture = "NONE"

            if results.multi_hand_landmarks:
                self.hand_detected = True
                self.last_seen_time = time.time()
                hand = results.multi_hand_landmarks[0]
                lm = hand.landmark

                # Use Middle Finger MCP (idx 9) as stable center of palm
                raw_x = float(lm[9].x)
                raw_y = float(lm[9].y)

                # Smooth coordinates with EMA filter (buttery smooth motion)
                self.smooth_x = self.smooth_x * 0.60 + raw_x * 0.40
                self.smooth_y = self.smooth_y * 0.60 + raw_y * 0.40
                self.palm_x = self.smooth_x
                self.palm_y = self.smooth_y

                # Lane determination with hysteresis (deadband buffer to stop edge-flickering)
                # Left lane entered < 0.36, exited > 0.40
                # Right lane entered > 0.64, exited < 0.60
                if self.active_lane == 0:
                    if self.palm_x > 0.40:
                        self.active_lane = 1
                elif self.active_lane == 2:
                    if self.palm_x < 0.60:
                        self.active_lane = 1
                else:  # Currently in Center lane
                    if self.palm_x < 0.36:
                        self.active_lane = 0
                    elif self.palm_x > 0.64:
                        self.active_lane = 2

                # Finger extension classification
                # Distance-based & angle-based check
                wrist = lm[0]
                index_extended = (lm[8].y < lm[6].y) and (math.hypot(lm[8].x - wrist.x, lm[8].y - wrist.y) > 0.18)
                middle_extended = (lm[12].y < lm[10].y) and (math.hypot(lm[12].x - wrist.x, lm[12].y - wrist.y) > 0.18)
                ring_extended = (lm[16].y < lm[14].y) and (math.hypot(lm[16].x - wrist.x, lm[16].y - wrist.y) > 0.16)
                pinky_extended = (lm[20].y < lm[18].y) and (math.hypot(lm[20].x - wrist.x, lm[20].y - wrist.y) > 0.14)

                extended_count = sum([index_extended, middle_extended, ring_extended, pinky_extended])

                # Thumb pointing upwards relative to thumb joints
                thumb_up = (lm[4].y < lm[3].y) and (lm[3].y < lm[2].y)

                # Gestures with natural fallback options:
                # 1. JUMP: Thumbs-up 👍 OR raising hand high in frame (palm_y < 0.28)
                if (thumb_up and extended_count <= 1) or (self.palm_y < 0.28):
                    detected_gesture = "THUMBS_UP"
                # 2. SLIDE: Closed fist ✊ OR lowering hand down in frame (palm_y > 0.72)
                elif (extended_count == 0 and not thumb_up) or (self.palm_y > 0.74):
                    detected_gesture = "FIST"
                # 3. OPEN PALM (Steer & Ready confirmation)
                elif extended_count >= 3:
                    detected_gesture = "OPEN_PALM"
                # 4. STEER (Standard hand in frame)
                else:
                    detected_gesture = "STEER"

                # Draw skeleton overlay
                self._draw_hud_overlays(frame, hand, w, h)

            self.gesture = detected_gesture

            # Render downscaled frame directly for Pygame PiP HUD (220 x 150)
            hud_w, hud_h = 220, 150
            small_frame = cv2.resize(frame, (hud_w, hud_h))
            rgb_hud = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            self.hud_surface = pygame.image.frombuffer(rgb_hud.tobytes(), (hud_w, hud_h), "RGB")

        except Exception as e:
            # Prevent camera or drawing glitch from crashing the game
            self.hand_detected = False
            self.gesture = "ERROR"

    def _draw_hud_overlays(self, frame, hand, w, h):
        """Draw lane guide zones and neon skeleton directly on the webcam HUD."""
        try:
            # Lane divider guides
            cv2.line(frame, (int(w * 0.38), 0), (int(w * 0.38), h), (70, 75, 95), 1)
            cv2.line(frame, (int(w * 0.62), 0), (int(w * 0.62), h), (70, 75, 95), 1)

            # Active lane highlight zone
            overlay = frame.copy()
            if self.active_lane == 0:
                cv2.rectangle(overlay, (0, 0), (int(w * 0.38), h), (0, 180, 240), -1)
            elif self.active_lane == 1:
                cv2.rectangle(overlay, (int(w * 0.38), 0), (int(w * 0.62), h), (0, 220, 130), -1)
            else:
                cv2.rectangle(overlay, (int(w * 0.62), 0), (w, h), (0, 180, 240), -1)
            cv2.addWeighted(overlay, 0.16, frame, 0.84, 0, frame)

            # Landmarks & Connections
            self.mp_draw.draw_landmarks(
                frame,
                hand,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_draw.DrawingSpec(color=(0, 255, 200), thickness=2, circle_radius=3),
                self.mp_draw.DrawingSpec(color=(255, 200, 50), thickness=2),
            )

            # Glowing palm cursor
            cx = int(max(0, min(w, self.palm_x * w)))
            cy = int(max(0, min(h, self.palm_y * h)))
            cv2.circle(frame, (cx, cy), 8, (0, 240, 255), -1)
            cv2.circle(frame, (cx, cy), 12, (255, 255, 255), 2)
        except Exception:
            pass


# -------------------------------------------------------------
# Particle & Visual FX System
# -------------------------------------------------------------
class Particle:
    def __init__(self, x, y, vx, vy, color, size, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = max(0.01, life)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self, screen):
        alpha = max(0.0, min(1.0, self.life / self.max_life))
        r = max(1, int(self.size * alpha))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), r)


class FloatingText:
    def __init__(self, text, x, y, color, size=24, duration=1.0):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.duration = duration
        self.life = duration

    def update(self, dt):
        self.y -= 45 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, screen, font_cache):
        alpha = max(0, min(255, int(255 * (self.life / self.duration))))
        font = font_cache.get(self.size, font_cache[22])
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        screen.blit(surf, surf.get_rect(center=(int(self.x), int(self.y))))


# -------------------------------------------------------------
# Obstacles & Collectibles
# -------------------------------------------------------------
class Obstacle:
    def __init__(self, lane, kind, speed):
        self.lane = lane
        self.kind = kind  # "BLOCK" (Hurdle) or "BARRIER" (Aerial beam)
        self.y = -70
        self.speed = speed
        self.passed = False

    def update(self, dt, current_speed):
        self.speed = current_speed
        self.y += self.speed * dt

    def draw(self, screen):
        x = LANE_X[self.lane]
        scale = max(0.55, min(1.4, 0.55 + (self.y / HEIGHT) * 0.9))

        if self.kind == "BLOCK":
            # Red Hurdle: Jump over
            w, h = int(95 * scale), int(60 * scale)
            rect = pygame.Rect(x - w // 2, int(self.y) - h // 2, w, h)
            pygame.draw.rect(screen, RED_NEON, rect, border_radius=8)
            pygame.draw.rect(screen, RED_GLOW, rect, 3, border_radius=8)
            stripe_y = rect.centery
            pygame.draw.line(screen, WHITE, (rect.left + 8, stripe_y), (rect.right - 8, stripe_y), 3)

        elif self.kind == "BARRIER":
            # Yellow Aerial Laser Beam: Slide under
            w, h = int(130 * scale), int(32 * scale)
            draw_y = int(self.y) - int(38 * scale)
            rect = pygame.Rect(x - w // 2, draw_y, w, h)
            pygame.draw.rect(screen, YELLOW_NEON, rect, border_radius=6)
            pygame.draw.rect(screen, (255, 255, 180), rect, 3, border_radius=6)
            pygame.draw.line(screen, (80, 60, 0), (rect.left + 10, rect.centery), (rect.right - 10, rect.centery), 4)

        elif self.kind == "PILLAR":
            # Purple Laser Column: Dodge sideways
            w, h = int(80 * scale), int(135 * scale)
            rect = pygame.Rect(x - w // 2, int(self.y) - h // 2, w, h)
            pygame.draw.rect(screen, PURPLE_NEON, rect, border_radius=10)
            pygame.draw.rect(screen, (220, 160, 255), rect, 3, border_radius=10)
            pygame.draw.circle(screen, WHITE, (x, rect.centery), int(12 * scale))


class Coin:
    def __init__(self, lane, speed):
        self.lane = lane
        self.y = -40
        self.speed = speed
        self.collected = False
        self.anim_offset = random.random() * math.pi * 2

    def update(self, dt, current_speed, player_pos=None, magnet_active=False):
        self.speed = current_speed
        self.anim_offset += dt * 6

        if magnet_active and player_pos:
            px, py = player_pos
            cx, cy = LANE_X[self.lane], self.y
            dist = math.hypot(px - cx, py - cy)
            if dist < 420:
                self.y += (py - cy) * 4.5 * dt
                return

        self.y += self.speed * dt

    def draw(self, screen):
        x = LANE_X[self.lane]
        scale = max(0.5, min(1.3, 0.5 + (self.y / HEIGHT) * 0.8))
        radius = max(6, int(16 * scale))

        w_factor = abs(math.cos(self.anim_offset))
        rx = max(4, int(radius * w_factor))
        ry = radius

        coin_rect = pygame.Rect(x - rx, int(self.y) - ry, rx * 2, ry * 2)
        pygame.draw.ellipse(screen, GOLD, coin_rect)
        pygame.draw.ellipse(screen, GOLD_LIGHT, coin_rect, 2)
        if rx > 6:
            pygame.draw.line(screen, (180, 120, 0), (x, int(self.y) - ry // 2), (x, int(self.y) + ry // 2), 2)


class PowerUp:
    def __init__(self, lane, kind, speed):
        self.lane = lane
        self.kind = kind  # 'SHIELD' or 'MAGNET'
        self.y = -50
        self.speed = speed
        self.collected = False
        self.anim_timer = 0.0

    def update(self, dt, current_speed):
        self.speed = current_speed
        self.y += self.speed * dt
        self.anim_timer += dt * 5

    def draw(self, screen):
        x = LANE_X[self.lane]
        scale = max(0.6, min(1.3, 0.6 + (self.y / HEIGHT) * 0.7))
        r = int(22 * scale)
        pulse = int(math.sin(self.anim_timer) * 3)

        color = BLUE_NEON if self.kind == "SHIELD" else PURPLE_NEON
        center = (x, int(self.y))
        pygame.draw.circle(screen, color, center, r + pulse)
        pygame.draw.circle(screen, WHITE, center, r - 4, 3)

        if self.kind == "SHIELD":
            pygame.draw.line(screen, WHITE, (x - 6, int(self.y)), (x + 6, int(self.y)), 3)
            pygame.draw.line(screen, WHITE, (x, int(self.y) - 6), (x, int(self.y) + 6), 3)
        else:
            pygame.draw.arc(screen, WHITE, pygame.Rect(x - 8, int(self.y) - 8, 16, 16), 0, math.pi, 3)


# -------------------------------------------------------------
# Main Game Engine
# -------------------------------------------------------------
class GameRunner:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Hand Gesture Runner [100% Hands-Free]")
        self.clock = pygame.time.Clock()

        # Fonts
        self.fonts = {
            14: pygame.font.SysFont("segoeui", 14),
            18: pygame.font.SysFont("segoeui", 18, bold=True),
            22: pygame.font.SysFont("segoeui", 22, bold=True),
            26: pygame.font.SysFont("segoeui", 26, bold=True),
            32: pygame.font.SysFont("segoeui", 32, bold=True),
            44: pygame.font.SysFont("segoeui", 44, bold=True),
            64: pygame.font.SysFont("segoeui", 64, bold=True),
        }

        self.sfx = SoundFX()
        self.gc = GestureController(camera_idx=0)
        self.highscore = self.load_highscore()

        # States
        self.state = STATE_READY
        self.gesture_hold_timer = 0.0

        # Countdown
        self.countdown_val = 3
        self.countdown_timer = 0.0

        # Player stats & physics
        self.player_lane = 1
        self.player_x = float(LANE_X[1])
        self.player_target_x = float(LANE_X[1])
        self.player_y = float(PLAYER_Y)

        self.is_jumping = False
        self.jump_timer = 0.0
        self.jump_duration = 0.75

        self.is_sliding = False
        self.slide_timer = 0.0
        self.slide_duration = 0.70

        self.action_cooldown = 0.0

        # Powerups
        self.has_shield = False
        self.magnet_timer = 0.0

        # Gameplay vars
        self.score = 0
        self.coins_collected = 0
        self.distance = 0.0
        self.speed = 280.0
        self.max_speed = 520.0
        self.grace_period = 0.0  # Safe runway after start

        # Entities
        self.obstacles = []
        self.coins = []
        self.powerups = []
        self.particles = []
        self.float_texts = []

        # Timers
        self.obstacle_timer = 0.0
        self.coin_timer = 0.0
        self.powerup_timer = 0.0
        self.road_scroll = 0.0

    def load_highscore(self):
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("highscore", 0)
        except Exception:
            pass
        return 0

    def save_highscore(self):
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                json.dump({"highscore": self.highscore}, f)
        except Exception:
            pass

    def reset_game(self):
        self.player_lane = 1
        self.player_x = float(LANE_X[1])
        self.player_target_x = float(LANE_X[1])
        self.is_jumping = False
        self.jump_timer = 0.0
        self.is_sliding = False
        self.slide_timer = 0.0
        self.action_cooldown = 0.0

        self.has_shield = False
        self.magnet_timer = 0.0

        self.score = 0
        self.coins_collected = 0
        self.distance = 0.0
        self.speed = 280.0
        self.grace_period = 3.2  # 3.2 seconds of obstacle-free runway!

        self.obstacles.clear()
        self.coins.clear()
        self.powerups.clear()
        self.particles.clear()
        self.float_texts.clear()

        self.obstacle_timer = 0.0
        self.coin_timer = 0.0
        self.powerup_timer = 0.0
        self.road_scroll = 0.0
        self.gesture_hold_timer = 0.0

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.08)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_r and self.state == STATE_GAMEOVER:
                        self.start_countdown()

            # Process Hand Gestures safely
            self.gc.process()

            # State Logic
            if self.state == STATE_READY:
                self.update_ready_state(dt)
            elif self.state == STATE_COUNTDOWN:
                self.update_countdown_state(dt)
            elif self.state == STATE_PLAYING:
                self.update_playing_state(dt)
            elif self.state == STATE_PAUSED:
                self.update_paused_state(dt)
            elif self.state == STATE_GAMEOVER:
                self.update_gameover_state(dt)

            # Particles & Floating Text updates
            self.particles = [p for p in self.particles if p.update(dt)]
            self.float_texts = [ft for ft in self.float_texts if ft.update(dt)]

            # Draw Screen
            self.draw()
            pygame.display.flip()

        self.gc.release()
        pygame.quit()

    # ---------------------------------------------------------
    # State Updates
    # ---------------------------------------------------------
    def update_ready_state(self, dt):
        """Show hand to start the run! Fast, responsive, zero-frustration."""
        if self.gc.hand_detected:
            self.gesture_hold_timer += dt
            # Short 0.8s hold is friendly and responsive
            if self.gesture_hold_timer >= 0.8:
                self.gesture_hold_timer = 0.0
                self.start_countdown()
        else:
            self.gesture_hold_timer = max(0.0, self.gesture_hold_timer - dt * 2.0)

    def start_countdown(self):
        self.reset_game()
        self.state = STATE_COUNTDOWN
        self.countdown_val = 3
        self.countdown_timer = 0.0
        self.sfx.play("tick")

    def update_countdown_state(self, dt):
        self.countdown_timer += dt
        if self.countdown_timer >= 0.75:
            self.countdown_timer = 0.0
            self.countdown_val -= 1
            if self.countdown_val > 0:
                self.sfx.play("tick")
            else:
                self.sfx.play("go")
                self.state = STATE_PLAYING

    def update_playing_state(self, dt):
        # 1. Hands-Free Auto-Pause if hand leaves camera view
        if not self.gc.hand_detected and (time.time() - self.gc.last_seen_time > 0.65):
            self.state = STATE_PAUSED
            return

        # 2. Smooth Lane Switching
        self.player_lane = self.gc.active_lane
        self.player_target_x = float(LANE_X[self.player_lane])

        # Smooth exponential easing between lanes (no snapping, 100% fluid)
        self.player_x += (self.player_target_x - self.player_x) * (1.0 - math.exp(-14.0 * dt))

        # 3. Gesture Actions (Jump & Slide)
        gesture = self.gc.gesture
        if self.action_cooldown <= 0:
            if gesture == "THUMBS_UP" and not self.is_jumping:
                self.is_jumping = True
                self.jump_timer = self.jump_duration
                self.is_sliding = False
                self.action_cooldown = 0.50
                self.sfx.play("jump")
                self.spawn_float_text("JUMP! 👍", self.player_x, PLAYER_Y - 90, CYAN)
                for _ in range(8):
                    self.particles.append(Particle(
                        self.player_x + random.uniform(-20, 20),
                        PLAYER_Y + 20,
                        random.uniform(-40, 40),
                        random.uniform(-60, -10),
                        CYAN, random.randint(3, 6), 0.4
                    ))

            elif gesture == "FIST" and not self.is_sliding:
                self.is_sliding = True
                self.slide_timer = self.slide_duration
                self.is_jumping = False
                self.action_cooldown = 0.45
                self.sfx.play("slide")
                self.spawn_float_text("SLIDE! ✊", self.player_x, PLAYER_Y + 10, YELLOW_NEON)
                for _ in range(8):
                    self.particles.append(Particle(
                        self.player_x + random.uniform(-30, 30),
                        PLAYER_Y + 30,
                        random.uniform(-80, 80),
                        random.uniform(-20, 10),
                        YELLOW_NEON, random.randint(2, 5), 0.35
                    ))
        else:
            self.action_cooldown -= dt

        # Update Jump & Slide Timers
        if self.is_jumping:
            self.jump_timer -= dt
            if self.jump_timer <= 0:
                self.is_jumping = False
        if self.is_sliding:
            self.slide_timer -= dt
            if self.slide_timer <= 0:
                self.is_sliding = False

        if self.magnet_timer > 0:
            self.magnet_timer -= dt

        # Grace period counter
        if self.grace_period > 0:
            self.grace_period -= dt

        # Movement, Speed & Progression
        self.distance += self.speed * dt
        self.road_scroll += self.speed * dt
        self.speed = min(self.max_speed, 280.0 + (self.distance / 50.0))
        self.score = int(self.distance / 8.0) + (self.coins_collected * 25)

        if self.score > self.highscore:
            self.highscore = self.score

        # Footstep dust particles
        if not self.is_jumping and random.random() < 0.35:
            self.particles.append(Particle(
                self.player_x + random.uniform(-15, 15),
                PLAYER_Y + 35,
                random.uniform(-15, 15),
                random.uniform(-20, 0),
                GRAY, random.randint(2, 4), 0.3
            ))

        # Obstacle & Item Spawning (Only after grace period)
        if self.grace_period <= 0:
            self.obstacle_timer += dt
            obs_interval = max(0.80, 1.55 - (self.distance / 12000.0))
            if self.obstacle_timer >= obs_interval:
                self.obstacle_timer = 0.0
                lane = random.randrange(3)
                types = ["BLOCK", "BARRIER"]
                if self.distance > 800:
                    types.append("PILLAR")
                kind = random.choice(types)
                self.obstacles.append(Obstacle(lane, kind, self.speed))

        # Coins Spawning
        self.coin_timer += dt
        if self.coin_timer >= 0.75:
            self.coin_timer = 0.0
            lane = random.randrange(3)
            for i in range(random.randint(1, 3)):
                coin = Coin(lane, self.speed)
                coin.y = -40 - (i * 55)
                self.coins.append(coin)

        # Powerup Spawning
        self.powerup_timer += dt
        if self.powerup_timer >= 12.0:
            self.powerup_timer = 0.0
            if random.random() < 0.65:
                kind = random.choice(["SHIELD", "MAGNET"])
                self.powerups.append(PowerUp(random.randrange(3), kind, self.speed))

        # Collision Calculation with smooth physical bounding box
        jump_offset = math.sin((1.0 - max(0.0, self.jump_timer / self.jump_duration)) * math.pi) * 85.0 if self.is_jumping else 0.0
        player_box_y = PLAYER_Y - jump_offset

        for ob in self.obstacles:
            ob.update(dt, self.speed)
            if not ob.passed and abs(ob.y - PLAYER_Y) < 45 and ob.lane == self.player_lane:
                safe = False
                if ob.kind == "BLOCK" and self.is_jumping and jump_offset > 35:
                    safe = True
                elif ob.kind == "BARRIER" and self.is_sliding:
                    safe = True

                if safe:
                    ob.passed = True
                    self.score += 50
                    self.spawn_float_text("+50 DODGE!", self.player_x, PLAYER_Y - 90, GREEN_NEON)
                else:
                    if self.has_shield:
                        self.has_shield = False
                        ob.passed = True
                        self.sfx.play("shield_break")
                        self.spawn_float_text("SHIELD BROKEN!", self.player_x, PLAYER_Y - 80, BLUE_NEON)
                        for _ in range(20):
                            self.particles.append(Particle(
                                self.player_x, PLAYER_Y,
                                random.uniform(-140, 140), random.uniform(-140, 140),
                                BLUE_NEON, random.randint(3, 7), 0.5
                            ))
                    else:
                        self.trigger_gameover()
                        return

        # Coin pickups
        magnet_on = (self.magnet_timer > 0)
        p_center = (self.player_x, player_box_y)
        for c in self.coins:
            c.update(dt, self.speed, player_pos=p_center, magnet_active=magnet_on)
            if not c.collected and abs(c.y - PLAYER_Y) < 45:
                coin_x = LANE_X[c.lane]
                if abs(coin_x - self.player_x) < 60:
                    c.collected = True
                    self.coins_collected += 1
                    self.sfx.play("coin")
                    self.spawn_float_text("+25", coin_x, c.y, GOLD)
                    for _ in range(8):
                        self.particles.append(Particle(
                            coin_x, c.y,
                            random.uniform(-60, 60), random.uniform(-60, 60),
                            GOLD, random.randint(2, 5), 0.4
                        ))

        # Powerup pickups
        for pu in self.powerups:
            pu.update(dt, self.speed)
            if not pu.collected and abs(pu.y - PLAYER_Y) < 45 and pu.lane == self.player_lane:
                pu.collected = True
                self.sfx.play("powerup")
                if pu.kind == "SHIELD":
                    self.has_shield = True
                    self.spawn_float_text("SHIELD ACQUIRED!", self.player_x, PLAYER_Y - 90, BLUE_NEON)
                else:
                    self.magnet_timer = 9.0
                    self.spawn_float_text("COIN MAGNET 9s!", self.player_x, PLAYER_Y - 90, PURPLE_NEON)

        # Offscreen cleanup
        self.obstacles = [o for o in self.obstacles if o.y < HEIGHT + 120]
        self.coins = [c for c in self.coins if c.y < HEIGHT + 60 and not c.collected]
        self.powerups = [pu for pu in self.powerups if pu.y < HEIGHT + 60 and not pu.collected]

    def trigger_gameover(self):
        self.state = STATE_GAMEOVER
        self.sfx.play("crash")
        self.save_highscore()
        self.gesture_hold_timer = 0.0
        for _ in range(35):
            self.particles.append(Particle(
                self.player_x, PLAYER_Y,
                random.uniform(-180, 180), random.uniform(-200, 80),
                random.choice([RED_NEON, GOLD, WHITE]), random.randint(3, 8), 0.7
            ))

    def update_paused_state(self, dt):
        """Auto-paused because hand was removed. Resumes cleanly when hand returns!"""
        if self.gc.hand_detected:
            self.gesture_hold_timer += dt
            if self.gesture_hold_timer >= 0.8:
                self.gesture_hold_timer = 0.0
                self.state = STATE_PLAYING
                self.sfx.play("go")
        else:
            self.gesture_hold_timer = 0.0

    def update_gameover_state(self, dt):
        """Hands-free restart! Just show hand to play again. (NEVER crashes or quits)."""
        if self.gc.hand_detected:
            self.gesture_hold_timer += dt
            if self.gesture_hold_timer >= 1.0:
                self.gesture_hold_timer = 0.0
                self.start_countdown()
        else:
            self.gesture_hold_timer = max(0.0, self.gesture_hold_timer - dt * 2.0)

    def spawn_float_text(self, text, x, y, color):
        self.float_texts.append(FloatingText(text, x, y, color))

    # ---------------------------------------------------------
    # Rendering
    # ---------------------------------------------------------
    def draw(self):
        self.screen.fill(BG_DARK)
        self.draw_environment()

        # Entities
        for c in self.coins:
            c.draw(self.screen)
        for pu in self.powerups:
            pu.draw(self.screen)
        for ob in self.obstacles:
            ob.draw(self.screen)

        # Player
        if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_COUNTDOWN):
            self.draw_player()

        # Particles & Texts
        for p in self.particles:
            p.draw(self.screen)
        for ft in self.float_texts:
            ft.draw(self.screen, self.fonts)

        # HUDs
        self.draw_top_hud()
        self.draw_camera_hud()

        # Screen Overlays
        if self.state == STATE_READY:
            self.draw_ready_overlay()
        elif self.state == STATE_COUNTDOWN:
            self.draw_countdown_overlay()
        elif self.state == STATE_PAUSED:
            self.draw_paused_overlay()
        elif self.state == STATE_GAMEOVER:
            self.draw_gameover_overlay()

    def draw_environment(self):
        horizon_y = 110
        pygame.draw.circle(self.screen, (35, 42, 68), (WIDTH // 2, horizon_y), 130)

        road_poly = [
            (WIDTH // 2 - 130, horizon_y),
            (WIDTH // 2 + 130, horizon_y),
            (WIDTH - 120, HEIGHT),
            (120, HEIGHT)
        ]
        pygame.draw.polygon(self.screen, ROAD_COLOR, road_poly)
        pygame.draw.line(self.screen, ROAD_BORDER, road_poly[0], road_poly[3], 4)
        pygame.draw.line(self.screen, ROAD_BORDER, road_poly[1], road_poly[2], 4)

        offset = int(self.road_scroll * 0.8) % 100
        for divider_x_norm in [-0.33, 0.33]:
            top_x = WIDTH // 2 + int(divider_x_norm * 130)
            bot_x = WIDTH // 2 + int(divider_x_norm * (WIDTH // 2 - 120))

            y = horizon_y - offset
            while y < HEIGHT:
                if y > horizon_y:
                    t = (y - horizon_y) / (HEIGHT - horizon_y)
                    cur_x = int(top_x + (bot_x - top_x) * t)
                    length = int(15 + 40 * t)
                    pygame.draw.line(self.screen, ROAD_LINE, (cur_x, y), (cur_x, y + length), max(2, int(4 * t)))
                y += 90

    def draw_player(self):
        px = int(self.player_x)
        jumping = self.is_jumping
        sliding = self.is_sliding

        # Parabolic physical jump height calculation
        jump_offset = 0.0
        if jumping:
            t = 1.0 - max(0.0, self.jump_timer / self.jump_duration)
            jump_offset = math.sin(t * math.pi) * 85.0

        py = PLAYER_Y - int(jump_offset)

        # Dynamic ground shadow (shrinks as player leaps higher)
        shadow_scale = max(0.45, 1.0 - (jump_offset / 120.0))
        shadow_w = int((64 if not sliding else 88) * shadow_scale)
        shadow_h = int(16 * shadow_scale)
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (10, 12, 18, 160), (0, 0, shadow_w, shadow_h))
        self.screen.blit(shadow_surf, (px - shadow_w // 2, PLAYER_Y + 36))

        # Shield aura
        if self.has_shield:
            shield_radius = 55 if not sliding else 42
            pygame.draw.circle(self.screen, (0, 180, 255), (px, py), shield_radius, 3)

        # Character model (Cyber Runner)
        if sliding:
            body_rect = pygame.Rect(px - 44, py + 12, 88, 36)
            pygame.draw.rect(self.screen, CYAN, body_rect, border_radius=12)
            pygame.draw.rect(self.screen, WHITE, body_rect, 2, border_radius=12)
            pygame.draw.circle(self.screen, WHITE, (px + 24, py + 26), 14)
            pygame.draw.circle(self.screen, BG_DARK, (px + 28, py + 24), 3)
        else:
            body_rect = pygame.Rect(px - 26, py - 46, 52, 92)
            pygame.draw.rect(self.screen, CYAN, body_rect, border_radius=14)
            pygame.draw.rect(self.screen, (180, 250, 255), body_rect, 2, border_radius=14)
            pygame.draw.circle(self.screen, WHITE, (px, body_rect.top + 16), 14)
            pygame.draw.rect(self.screen, BG_DARK, (px - 10, body_rect.top + 12, 20, 7), border_radius=3)
            pygame.draw.line(self.screen, GREEN_NEON, (px - 8, body_rect.top + 15), (px + 8, body_rect.top + 15), 2)

        # Magnet effect ring
        if self.magnet_timer > 0:
            aura_r = int(48 + math.sin(time.time() * 10) * 5)
            pygame.draw.circle(self.screen, (180, 70, 255), (px, py), aura_r, 2)

    def draw_top_hud(self):
        bar = pygame.Surface((WIDTH, 70), pygame.SRCALPHA)
        bar.fill(DARK_PANEL)
        self.screen.blit(bar, (0, 0))

        score_txt = self.fonts[26].render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (25, 12))

        coins_txt = self.fonts[22].render(f"COINS: {self.coins_collected}", True, GOLD)
        self.screen.blit(coins_txt, (25, 40))

        hi_txt = self.fonts[22].render(f"BEST: {self.highscore}", True, PURPLE_NEON)
        self.screen.blit(hi_txt, (260, 15))

        if self.has_shield:
            badge = self.fonts[18].render("[ SHIELD ACTIVE ]", True, BLUE_NEON)
            self.screen.blit(badge, (420, 16))
        if self.magnet_timer > 0:
            m_txt = self.fonts[18].render(f"[ MAGNET {int(self.magnet_timer)}s ]", True, PURPLE_NEON)
            self.screen.blit(m_txt, (420, 40))

    def draw_camera_hud(self):
        hud_w, hud_h = 220, 150
        hud_x, hud_y = WIDTH - hud_w - 20, 15

        border_rect = pygame.Rect(hud_x - 3, hud_y - 3, hud_w + 6, hud_h + 38)
        pygame.draw.rect(self.screen, (40, 50, 75), border_rect, border_radius=10)

        if self.gc.hud_surface:
            self.screen.blit(self.gc.hud_surface, (hud_x, hud_y))
        else:
            ph = pygame.Surface((hud_w, hud_h))
            ph.fill((25, 30, 45))
            self.screen.blit(ph, (hud_x, hud_y))
            warn = self.fonts[14].render("Connecting Camera...", True, GRAY)
            self.screen.blit(warn, warn.get_rect(center=(hud_x + hud_w // 2, hud_y + hud_h // 2)))

        badge_rect = pygame.Rect(hud_x, hud_y + hud_h, hud_w, 32)
        pygame.draw.rect(self.screen, (20, 24, 38), badge_rect, border_bottom_left_radius=8, border_bottom_right_radius=8)

        gesture = self.gc.gesture
        if not self.gc.hand_detected:
            color = RED_NEON
            text = "NO HAND DETECTED"
        elif gesture == "THUMBS_UP":
            color = GREEN_NEON
            text = "👍 JUMP DETECTED"
        elif gesture == "FIST":
            color = YELLOW_NEON
            text = "✊ SLIDE DETECTED"
        elif gesture == "OPEN_PALM":
            color = CYAN
            text = "✋ OPEN PALM"
        else:
            color = WHITE
            lane_names = ["LEFT", "CENTER", "RIGHT"]
            text = f"✋ {lane_names[self.gc.active_lane]} LANE"

        txt_surf = self.fonts[14].render(text, True, color)
        self.screen.blit(txt_surf, txt_surf.get_rect(center=badge_rect.center))

    def draw_ready_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 25, 205))
        self.screen.blit(overlay, (0, 0))

        cx, cy = WIDTH // 2, HEIGHT // 2 - 40

        title = self.fonts[64].render("HAND GESTURE RUNNER", True, CYAN)
        self.screen.blit(title, title.get_rect(center=(cx, cy - 100)))

        sub = self.fonts[26].render("100% Hands-Free Motion Game", True, WHITE)
        self.screen.blit(sub, sub.get_rect(center=(cx, cy - 45)))

        cards = [
            ("Move Hand Left / Right", "STEER BETWEEN LANES"),
            ("Thumbs-Up 👍 (or Raise Hand)", "JUMP OVER RED HURDLES"),
            ("Closed Fist ✊ (or Lower Hand)", "SLIDE UNDER YELLOW BEAMS"),
            ("Remove Hand from View", "AUTO-PAUSES GAME"),
        ]
        card_y = cy + 20
        for gesture_title, desc in cards:
            g_surf = self.fonts[22].render(gesture_title, True, GOLD)
            d_surf = self.fonts[18].render(desc, True, GRAY)
            self.screen.blit(g_surf, (cx - 260, card_y))
            self.screen.blit(d_surf, (cx + 30, card_y + 2))
            card_y += 36

        start_y = cy + 195
        if not self.gc.hand_detected:
            prompt = self.fonts[26].render("👋 Show your hand to the camera to begin", True, RED_NEON)
            self.screen.blit(prompt, prompt.get_rect(center=(cx, start_y)))
        else:
            prompt = self.fonts[26].render("Hand Detected! Starting game...", True, GREEN_NEON)
            self.screen.blit(prompt, prompt.get_rect(center=(cx, start_y)))

            progress = min(1.0, self.gesture_hold_timer / 0.8)
            self.draw_progress_ring(cx, start_y + 55, 30, progress, GREEN_NEON)

    def draw_countdown_overlay(self):
        cx, cy = WIDTH // 2, HEIGHT // 2
        txt = str(self.countdown_val) if self.countdown_val > 0 else "GO!"
        color = GREEN_NEON if self.countdown_val <= 0 else GOLD
        surf = self.fonts[64].render(txt, True, color)
        self.screen.blit(surf, surf.get_rect(center=(cx, cy)))

    def draw_paused_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 25, 215))
        self.screen.blit(overlay, (0, 0))

        cx, cy = WIDTH // 2, HEIGHT // 2
        title = self.fonts[44].render("GAME PAUSED", True, YELLOW_NEON)
        self.screen.blit(title, title.get_rect(center=(cx, cy - 50)))

        msg = self.fonts[22].render("Place hand back in camera view to resume", True, WHITE)
        self.screen.blit(msg, msg.get_rect(center=(cx, cy + 10)))

        if self.gc.hand_detected:
            progress = min(1.0, self.gesture_hold_timer / 0.8)
            self.draw_progress_ring(cx, cy + 65, 26, progress, GREEN_NEON)

    def draw_gameover_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 10, 20, 220))
        self.screen.blit(overlay, (0, 0))

        cx, cy = WIDTH // 2, HEIGHT // 2 - 40

        title = self.fonts[64].render("GAME OVER", True, RED_NEON)
        self.screen.blit(title, title.get_rect(center=(cx, cy - 80)))

        score_txt = self.fonts[32].render(f"Final Score: {self.score}", True, WHITE)
        self.screen.blit(score_txt, score_txt.get_rect(center=(cx, cy - 15)))

        stats_txt = self.fonts[22].render(f"Coins: {self.coins_collected}   |   Best: {self.highscore}", True, GOLD)
        self.screen.blit(stats_txt, stats_txt.get_rect(center=(cx, cy + 30)))

        # Clean, pleasant hands-free restart (NO quitting)
        restart_prompt = self.fonts[22].render("Show Hand ✋ to PLAY AGAIN", True, GREEN_NEON)
        self.screen.blit(restart_prompt, restart_prompt.get_rect(center=(cx, cy + 100)))

        if self.gc.hand_detected:
            prog = min(1.0, self.gesture_hold_timer / 1.0)
            self.draw_progress_ring(cx, cy + 160, 28, prog, GREEN_NEON)
            label = self.fonts[14].render(f"Restarting... {int(prog * 100)}%", True, GREEN_NEON)
            self.screen.blit(label, label.get_rect(center=(cx, cy + 200)))

    def draw_progress_ring(self, cx, cy, radius, progress, color):
        """Draws a smooth circular progress indicator."""
        pygame.draw.circle(self.screen, (50, 60, 80), (int(cx), int(cy)), radius, 4)
        if progress > 0.02:
            num_points = max(3, int(progress * 48))
            points = []
            for i in range(num_points + 1):
                angle = -math.pi / 2 + (2 * math.pi * progress) * (i / num_points)
                px = int(cx + math.cos(angle) * radius)
                py = int(cy + math.sin(angle) * radius)
                points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(self.screen, color, False, points, 5)


# -------------------------------------------------------------
# Launcher Entry Point
# -------------------------------------------------------------
if __name__ == "__main__":
    try:
        game = GameRunner()
        game.run()
    except Exception as exc:
        print(f"\n[FATAL ERROR]: {exc}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
