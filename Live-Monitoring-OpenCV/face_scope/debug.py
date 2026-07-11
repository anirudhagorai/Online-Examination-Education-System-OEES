"""
debug_yolo.py — See exactly what YOLO detects in real time
═══════════════════════════════════════════════════════════
Run this to diagnose why phone/earphone isn't being detected.
Shows ALL detections with their class names and confidence scores
so you can see what YOLO actually sees.

Run:
    python debug_yolo.py

Press Q to quit, S to save a snapshot of current frame.
"""

import cv2
import time
from ultralytics import YOLO

# ── Load model ────────────────────────────────────────────────────────────────
print("Loading YOLOv8s...")
model = YOLO("yolov8s.pt")
print("Model loaded.\n")

# All COCO classes that could indicate cheating
CHEAT_CLASSES = {
    67: ("cell phone",    (0,  50, 255)),   # red
    65: ("remote",        (0,  80, 255)),   # red-orange (misclassified phones)
    63: ("laptop",        (0, 100, 200)),   # orange
    73: ("book",          (50,150, 255)),   # light red
    76: ("scissors",      (0, 200, 200)),   # yellow (sometimes earphones)
    84: ("book",          (50,150, 255)),
     0: ("person",        (0, 200,  80)),   # green
}

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera.")
    exit()

snap_id = 0
print("Camera open. Hold phone/earphone in front of camera.")
print("Watching for ALL detections — check terminal for class names.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w  = frame.shape[:2]

    # Run YOLO at very low confidence so we see everything
    results = model(frame, conf=0.15, imgsz=640, verbose=False)[0]

    cheat_found   = []
    all_detections= []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])
        label  = model.names[cls_id]
        x1,y1,x2,y2 = map(int, box.xyxy[0])

        all_detections.append((cls_id, label, conf))

        # Highlight cheating-relevant objects
        if cls_id in CHEAT_CLASSES:
            name, col = CHEAT_CLASSES[cls_id]
            cheat_found.append((cls_id, name, conf))
            # Draw thick colored box
            cv2.rectangle(frame,(x1,y1),(x2,y2),col,3)
            # Label with background
            txt = f"{label} {conf:.0%} [id:{cls_id}]"
            (tw,th),_ = cv2.getTextSize(txt,cv2.FONT_HERSHEY_SIMPLEX,0.55,2)
            cv2.rectangle(frame,(x1,y1-th-8),(x1+tw+6,y1),col,-1)
            cv2.putText(frame,txt,(x1+3,y1-4),
                        cv2.FONT_HERSHEY_SIMPLEX,0.55,(255,255,255),2,cv2.LINE_AA)
        else:
            # Draw thin grey box for other objects
            cv2.rectangle(frame,(x1,y1),(x2,y2),(60,60,60),1)
            cv2.putText(frame,f"{label} {conf:.0%}",
                        (x1,y1-4),cv2.FONT_HERSHEY_SIMPLEX,0.4,(80,80,80),1)

    # ── HUD ───────────────────────────────────────────────────────────────────
    ov = frame.copy()
    cv2.rectangle(ov,(0,0),(w,52),(12,14,20),-1)
    cv2.addWeighted(ov,0.8,frame,0.2,0,frame)

    total = len(all_detections)
    cheat = len(cheat_found)
    cv2.putText(frame,f"All detections: {total}  |  Cheat-relevant: {cheat}",
                (8,22),cv2.FONT_HERSHEY_SIMPLEX,0.55,(200,200,200),1,cv2.LINE_AA)
    cv2.putText(frame,"conf=0.15 (very sensitive)  |  Q=Quit  S=Snapshot",
                (8,42),cv2.FONT_HERSHEY_SIMPLEX,0.42,(100,100,120),1,cv2.LINE_AA)

    # Status strip
    ov2 = frame.copy()
    cv2.rectangle(ov2,(0,h-40),(w,h),(12,14,20),-1)
    cv2.addWeighted(ov2,0.8,frame,0.2,0,frame)

    if cheat_found:
        msg = "  DETECTED: " + ", ".join(f"{n}({c:.0%})" for _,n,c in cheat_found)
        cv2.putText(frame,msg,(8,h-10),cv2.FONT_HERSHEY_SIMPLEX,0.52,(0,100,255),2,cv2.LINE_AA)
    else:
        cv2.putText(frame,"  Nothing cheat-relevant detected — try holding phone closer",
                    (8,h-10),cv2.FONT_HERSHEY_SIMPLEX,0.44,(80,80,100),1,cv2.LINE_AA)

    cv2.imshow("YOLO Debug — All Detections  [Q=Quit  S=Snapshot]", frame)

    # Print to terminal every 2 seconds
    if int(time.time()) % 2 == 0:
        if all_detections:
            unique = {}
            for cid,lbl,cf in all_detections:
                if cid not in unique or cf > unique[cid][1]:
                    unique[cid] = (lbl,cf)
            classes_str = ", ".join(f"{lbl}({cf:.0%})[{cid}]"
                                    for cid,(lbl,cf) in sorted(unique.items(),key=lambda x:-x[1][1]))
            print(f"[{time.strftime('%H:%M:%S')}] Detected: {classes_str}")

    key = cv2.waitKey(1) & 0xFF
    if key in (ord('q'),ord('Q')):
        break
    elif key in (ord('s'),ord('S')):
        fname = f"yolo_debug_{snap_id:03d}.jpg"
        cv2.imwrite(fname, frame)
        snap_id += 1
        print(f"Saved {fname}")

cap.release()
cv2.destroyAllWindows()

print("\n── Summary ─────────────────────────────────────────")
print("If phone was NOT detected:")
print("  → YOLOv8s doesn't recognise that phone angle/color")
print("  → Solution: use a custom trained model")
print("")
print("If phone WAS detected but wrong class (e.g. 'remote'):")
print("  → Add that class ID to CHEAT_CLASSES in server.py")
print("──────────────────────────────────────────────────────")