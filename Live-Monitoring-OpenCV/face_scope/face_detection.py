"""
Face, Eyes & Movement Detection using OpenCV
============================================
Features:
  - Real-time face detection (Haar Cascade)
  - Eye detection within each face ROI
  - Head/face movement tracking (direction: Left, Right, Up, Down, Center)
  - FPS counter
  - On-screen stats overlay

Requirements:
  pip install opencv-python numpy

Usage:
  python face_detection.py
  Press 'q' to quit, 's' to save a snapshot.
"""

import cv2
import numpy as np
import time
import os

# ── Load Haar Cascades ──────────────────────────────────────────────────────
# These XML files ship with every opencv-python install.
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eye_cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

if face_cascade.empty() or eye_cascade.empty():
    raise RuntimeError("Could not load Haar cascade XML files. "
                       "Make sure opencv-python is properly installed.")


# ── Movement Tracker ────────────────────────────────────────────────────────
class MovementTracker:
    """Tracks face centre across frames and infers movement direction."""

    HISTORY   = 8        # frames to smooth over
    THRESHOLD = 18       # pixels of net displacement to call it "movement"

    def __init__(self, frame_w, frame_h):
        self.frame_w  = frame_w
        self.frame_h  = frame_h
        self.history  = []          # list of (cx, cy)
        self.direction = "Center"
        self.trail     = []         # raw centres for drawing trail

    def update(self, cx, cy):
        self.history.append((cx, cy))
        self.trail.append((cx, cy))
        if len(self.history) > self.HISTORY:
            self.history.pop(0)
        if len(self.trail) > 30:
            self.trail.pop(0)

        if len(self.history) >= 2:
            ox, oy = self.history[0]
            dx = cx - ox
            dy = cy - oy

            if abs(dx) < self.THRESHOLD and abs(dy) < self.THRESHOLD:
                self.direction = "Center (Still)"
            else:
                parts = []
                if abs(dy) >= self.THRESHOLD:
                    parts.append("Up"   if dy < 0 else "Down")
                if abs(dx) >= self.THRESHOLD:
                    parts.append("Left" if dx < 0 else "Right")
                self.direction = " + ".join(parts) if parts else "Center (Still)"

    def draw_trail(self, frame):
        for i in range(1, len(self.trail)):
            if self.trail[i - 1] is None or self.trail[i] is None:
                continue
            alpha = i / len(self.trail)
            color = (int(255 * alpha), int(100 * alpha), int(255 * (1 - alpha)))
            cv2.line(frame, self.trail[i - 1], self.trail[i], color, 2)


# ── Drawing helpers ──────────────────────────────────────────────────────────
def draw_corner_rect(img, rect, color=(0, 230, 118), thickness=2, corner_len=18):
    """Draw a stylised corner-only bounding box."""
    x, y, w, h = rect
    # Top-left
    cv2.line(img, (x, y),         (x + corner_len, y),         color, thickness)
    cv2.line(img, (x, y),         (x, y + corner_len),         color, thickness)
    # Top-right
    cv2.line(img, (x + w, y),     (x + w - corner_len, y),     color, thickness)
    cv2.line(img, (x + w, y),     (x + w, y + corner_len),     color, thickness)
    # Bottom-left
    cv2.line(img, (x, y + h),     (x + corner_len, y + h),     color, thickness)
    cv2.line(img, (x, y + h),     (x, y + h - corner_len),     color, thickness)
    # Bottom-right
    cv2.line(img, (x + w, y + h), (x + w - corner_len, y + h), color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - corner_len), color, thickness)


def put_label(img, text, pos, font_scale=0.55, color=(255, 255, 255),
              bg_color=(30, 30, 30), thickness=1):
    """Text with a dark background pill for readability."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = pos
    pad = 4
    cv2.rectangle(img,
                  (x - pad, y - th - pad),
                  (x + tw + pad, y + baseline + pad),
                  bg_color, -1)
    cv2.putText(img, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)


def draw_hud(frame, fps, face_count, direction, w, h):
    """Bottom HUD bar with stats."""
    bar_h = 40
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - bar_h), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    font   = cv2.FONT_HERSHEY_SIMPLEX
    y_text = h - 12
    cv2.putText(frame, f"FPS: {fps:.1f}",           (10,      y_text), font, 0.55, (100, 255, 100), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Faces: {face_count}",      (130,     y_text), font, 0.55, (100, 200, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Move: {direction}",        (240,     y_text), font, 0.55, (255, 200,  80), 1, cv2.LINE_AA)
    cv2.putText(frame, "Q=Quit  S=Snapshot",        (w - 185, y_text), font, 0.45, (160, 160, 160), 1, cv2.LINE_AA)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check that a camera is connected.")
        return

    ret, test_frame = cap.read()
    if not ret:
        print("[ERROR] Cannot read from webcam.")
        cap.release()
        return

    h, w = test_frame.shape[:2]
    tracker = MovementTracker(w, h)

    prev_time   = time.time()
    snapshot_id = 0

    print("[INFO] Face + Eye + Movement Detection started.")
    print("       Press 'q' to quit, 's' to save a snapshot.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)          # mirror — feels more natural
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray  = cv2.equalizeHist(gray)      # improve contrast for detection

        # ── Face detection ──────────────────────────────────────────────────
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor  = 1.1,
            minNeighbors = 5,
            minSize      = (60, 60),
            flags        = cv2.CASCADE_SCALE_IMAGE
        )

        face_count = len(faces)

        for idx, (fx, fy, fw, fh) in enumerate(faces):
            cx = fx + fw // 2
            cy = fy + fh // 2

            # Update tracker only for the first (largest) face
            if idx == 0:
                tracker.update(cx, cy)

            # Draw face box
            draw_corner_rect(frame, (fx, fy, fw, fh),
                             color=(0, 230, 118), thickness=2, corner_len=20)
            put_label(frame, f"Face {idx + 1}", (fx, fy - 6),
                      color=(0, 230, 118), bg_color=(0, 60, 30))

            # Centre dot
            cv2.circle(frame, (cx, cy), 4, (0, 230, 118), -1)

            # ── Eye detection inside face ROI ────────────────────────────
            roi_gray  = gray [fy:fy + fh, fx:fx + fw]
            roi_color = frame[fy:fy + fh, fx:fx + fw]

            eyes = eye_cascade.detectMultiScale(
                roi_gray,
                scaleFactor  = 1.05,
                minNeighbors = 6,
                minSize      = (20, 20)
            )

            for (ex, ey, ew, eh) in eyes:
                # Draw ellipse around each eye
                ecx = ex + ew // 2
                ecy = ey + eh // 2
                cv2.ellipse(roi_color, (ecx, ecy), (ew // 2, eh // 2),
                            0, 0, 360, (80, 180, 255), 2)
                cv2.circle(roi_color, (ecx, ecy), 2, (80, 180, 255), -1)

        # ── Movement trail ───────────────────────────────────────────────────
        tracker.draw_trail(frame)

        # ── Movement direction arrow ─────────────────────────────────────────
        direction = tracker.direction
        if "Left" in direction or "Right" in direction or "Up" in direction or "Down" in direction:
            arrow_x, arrow_y = w - 60, 60
            arrow_map = {
                "Left":  (-30, 0), "Right": (30, 0),
                "Up":    (0, -30), "Down":  (0, 30),
            }
            for key, (dx, dy) in arrow_map.items():
                if key in direction:
                    cv2.arrowedLine(frame,
                                   (arrow_x, arrow_y),
                                   (arrow_x + dx, arrow_y + dy),
                                   (255, 200, 80), 3, tipLength=0.4)

        # ── FPS ──────────────────────────────────────────────────────────────
        now = time.time()
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        # ── HUD ──────────────────────────────────────────────────────────────
        draw_hud(frame, fps,  face_count, direction, w, h)

        cv2.imshow("Face | Eyes | Movement Detection  —  Press Q to quit", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            fname = f"snapshot_{snapshot_id:03d}.jpg"
            cv2.imwrite(fname, frame)
            snapshot_id += 1
            print(f"[INFO] Snapshot saved → {fname}")

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Detection stopped.")


if __name__ == "__main__":
    main()
