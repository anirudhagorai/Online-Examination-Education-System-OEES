"""
server.py — ProctorScope Multi-Student Proctoring Server
════════════════════════════════════════════════════════════════════════════════
Runs 4 independent student camera feeds (USB or browser), detects faces/eyes/
movement/phones/earphones, logs violations, and serves a hardcoded exam
(edit the EXAM dict below to change questions).

Routes:
  GET  /                    → dashboard.html (proctor)
  GET  /join/<id>           → browser camera + exam page for student <id>
  GET  /exam/<id>           → exam.html (student opens on their own PC)
  GET  /stream/<id>         → MJPEG stream for student <id>
  GET  /api/status          → JSON: all students + global violations
  GET  /api/exam            → fallback: most recent exam
  GET  /api/exam/<id>       → exam currently scheduled for student <id>
  POST /api/event/<id>      → violation from student browser
  POST /api/submit/<id>     → student submits exam answers
  POST /browser_frame/<id>  → JPEG frame from student's browser camera

Install:
    pip install opencv-python numpy ultralytics

Run:
    python server.py

Proctor:  http://localhost:5000
Students: http://YOUR_IP:5000/exam/0   (USB camera on this PC)
          http://YOUR_IP:5000/join/1   (student's own device camera)
"""

import cv2
import os
import time
import json
import threading
import socket as _socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
from collections import deque, Counter
import numpy as _np

# ══════════════════════════════════════════════════════════════════════════════
# EXAM — hardcoded directly here, no external storage needed.
# Edit this dict to change questions, marks, and duration.
# ══════════════════════════════════════════════════════════════════════════════
EXAM = {
    "id": "exam-1",
    "title": "Computer Science — Unit 3 Assessment",
    "duration_minutes": 45,
    "total_marks": 14,
    "questions": [
        {"id":1,"text":"What does CPU stand for?","marks":2,
         "options":["Central Processing Unit","Computer Personal Unit","Central Program Utility","Core Processing Unit"],
         "correct":0},
        {"id":2,"text":"Which of the following is NOT a programming language?","marks":2,
         "options":["Python","Photoshop","JavaScript","Java"],
         "correct":1},
        {"id":3,"text":"What does HTML stand for?","marks":2,
         "options":["Hyper Transfer Markup Language","HyperText Markup Language","High Text Machine Language","Hyper Tool Multi Language"],
         "correct":1},
        {"id":4,"text":"Which data structure works on a LIFO principle?","marks":3,
         "options":["Queue","Array","Stack","Linked List"],
         "correct":2},
        {"id":5,"text":"What is the binary representation of decimal 10?","marks":3,
         "options":["1010","1100","1001","0110"],
         "correct":0},
        {"id":6,"text":"Which sorting algorithm has the best average-case complexity?","marks":3,
         "options":["Bubble Sort","Selection Sort","Merge Sort","Insertion Sort"],
         "correct":2},
        {"id":7,"text":"What does RAM stand for?","marks":2,
         "options":["Random Access Memory","Read And Modify","Rapid Array Module","Runtime Access Module"],
         "correct":0},
        {"id":8,"text":"In Python, which keyword defines a function?","marks":2,
         "options":["func","define","def","function"],
         "correct":2},
    ]
}

# In-memory submissions — resets when the server restarts.
# Structure: [{"exam_id","student_id","student_name","answers","submitted_at","violation_count"}]
_submissions_lock = threading.Lock()
submissions = []

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — STUDENT CONFIGURATION
# "src" options:  0,1,2,3 (USB webcam index)  |  "browser" (student's own device)
# ══════════════════════════════════════════════════════════════════════════════
STUDENTS = {
    0: {"name": "Student 1", "src": 0},
    1: {"name": "Student 2", "src": "browser"},
    2: {"name": "Student 3", "src": "browser"},
    3: {"name": "Student 4", "src": "browser"},
}

ABSENT_ALERT_SECS = 20
MULTI_ALERT_SECS  = 10
OBJECT_ALERT_SECS = 3

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — HAAR CASCADES
# ══════════════════════════════════════════════════════════════════════════════
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Face cascade not found. Run: pip install --upgrade opencv-python")

_ext = cv2.data.haarcascades + "haarcascade_eye_tree_extended.xml"
_std = cv2.data.haarcascades + "haarcascade_eye.xml"
eye_cascade = cv2.CascadeClassifier(_ext if os.path.exists(_ext) else _std)
if eye_cascade.empty():
    raise RuntimeError("Eye cascade not found. Run: pip install --upgrade opencv-python")
print(f"[INFO] Eye cascade: {'extended' if os.path.exists(_ext) else 'standard'}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2B — YOLO OBJECT DETECTOR (phone + earphone)
# ══════════════════════════════════════════════════════════════════════════════
try:
    from ultralytics import YOLO as _YOLO
    _yolo_model  = _YOLO("yolov8s.pt")
    YOLO_ENABLED = True
    print("[INFO] YOLOv8s loaded — phone + earphone detection active")
except ImportError:
    YOLO_ENABLED = False
    print("[WARN] ultralytics not installed — run: pip install ultralytics")
except Exception as e:
    YOLO_ENABLED = False
    print(f"[WARN] YOLO load failed ({e})")

_PHONE_CLASS_ID = 67
_COL_PHONE      = (0, 50, 255)
_COL_EARPHONE   = (0, 160, 255)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — STABILISERS
# ══════════════════════════════════════════════════════════════════════════════
class Stabiliser:
    def __init__(self, window=10):
        self._h = deque(maxlen=window)
    def update(self, v):
        self._h.append(v)
        return Counter(self._h).most_common(1)[0][0]

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — MOVEMENT TRACKER
# ══════════════════════════════════════════════════════════════════════════════
class MovementTracker:
    HISTORY = 8; THRESHOLD = 18
    def __init__(self):
        self.history=[]; self.trail=[]; self.direction="Center"
    def update(self, cx, cy):
        self.history.append((cx,cy)); self.trail.append((cx,cy))
        if len(self.history)>self.HISTORY: self.history.pop(0)
        if len(self.trail)>30: self.trail.pop(0)
        if len(self.history)>=2:
            ox,oy=self.history[0]; dx,dy=cx-ox,cy-oy
            if abs(dx)<self.THRESHOLD and abs(dy)<self.THRESHOLD:
                self.direction="Center"
            else:
                parts=[]
                if abs(dy)>=self.THRESHOLD: parts.append("Up" if dy<0 else "Down")
                if abs(dx)>=self.THRESHOLD: parts.append("Left" if dx<0 else "Right")
                self.direction=" + ".join(parts) or "Center"
    def draw_trail(self, frame):
        for i in range(1,len(self.trail)):
            if not self.trail[i-1] or not self.trail[i]: continue
            a=i/len(self.trail)
            cv2.line(frame,self.trail[i-1],self.trail[i],(int(255*a),int(100*a),int(255*(1-a))),1)
    def reset(self):
        self.history=[]; self.trail=[]; self.direction="Center"

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — DRAWING HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _corner_rect(img, rect, color, thick=2, cl=16):
    x,y,w,h=rect
    for p in [((x,y),(x+cl,y)),((x,y),(x,y+cl)),
              ((x+w,y),(x+w-cl,y)),((x+w,y),(x+w,y+cl)),
              ((x,y+h),(x+cl,y+h)),((x,y+h),(x,y+h-cl)),
              ((x+w,y+h),(x+w-cl,y+h)),((x+w,y+h),(x+w,y+h-cl))]:
        cv2.line(img,p[0],p[1],color,thick)

def _label(img, text, pos, scale=0.45, color=(255,255,255), bg=(20,20,20)):
    f=cv2.FONT_HERSHEY_SIMPLEX
    (tw,th),bl=cv2.getTextSize(text,f,scale,1)
    x,y=pos; p=3
    cv2.rectangle(img,(x-p,y-th-p),(x+tw+p,y+bl+p),bg,-1)
    cv2.putText(img,text,(x,y),f,scale,color,1,cv2.LINE_AA)

def _status_banner(frame, n, name, w):
    ov=frame.copy()
    if n==0: col,msg=(0,50,220), f"NO FACE — {name}"
    elif n==1: col,msg=(0,200,80), f"FACE OK — {name}"
    else: col,msg=(0,150,255), f"MULTI FACE:{n} — {name}"
    cv2.rectangle(ov,(0,0),(w,32),col,-1)
    cv2.addWeighted(ov,0.7,frame,0.3,0,frame)
    cv2.putText(frame,msg,(7,22),cv2.FONT_HERSHEY_SIMPLEX,0.52,(255,255,255),2,cv2.LINE_AA)

def _hud(frame, fps, faces, eyes, direction, w, h, viols):
    ov=frame.copy()
    cv2.rectangle(ov,(0,h-36),(w,h),(10,12,18),-1)
    cv2.addWeighted(ov,0.7,frame,0.3,0,frame)
    f=cv2.FONT_HERSHEY_SIMPLEX; y=h-8
    cv2.putText(frame,f"FPS:{fps:.0f}",(6,y),f,0.42,(100,255,100),1,cv2.LINE_AA)
    cv2.putText(frame,f"F:{faces} E:{eyes}",(70,y),f,0.42,(100,200,255),1,cv2.LINE_AA)
    cv2.putText(frame,f"{direction}",(150,y),f,0.42,(255,200,80),1,cv2.LINE_AA)
    cv2.putText(frame,f"V:{viols}",(w-55,y),f,0.42,(255,80,80),1,cv2.LINE_AA)

def _detect_eyes(gray, frame, fx, fy, fw, fh):
    eys=int(fh*0.20); eye_end=int(fh*0.45); roi_h=eye_end-eys
    if roi_h<=0 or fw<=0: return 0
    rg=gray[fy+eys:fy+eye_end, fx:fx+fw]
    rc=frame[fy+eys:fy+eye_end, fx:fx+fw]
    if rg.size==0: return 0
    raw=eye_cascade.detectMultiScale(rg,1.1,15,minSize=(20,20),
        maxSize=(int(fw*0.45),int(roi_h*0.85)))
    valid=[]
    if len(raw)>=2:
        sr=sorted(raw,key=lambda e:e[0]); best,bdy=None,9999
        for i in range(len(sr)):
            for j in range(i+1,len(sr)):
                e1,e2=sr[i],sr[j]
                dy=abs((e1[1]+e1[3]//2)-(e2[1]+e2[3]//2))
                if dy<bdy: bdy,best=dy,[e1,e2]
        if best and bdy<roi_h*0.30: valid=best
    elif len(raw)==1: valid=list(raw)
    for (ex,ey,ew,eh) in valid:
        ecx,ecy=ex+ew//2,ey+eh//2
        cv2.ellipse(rc,(ecx,ecy),(ew//2,eh//2),0,0,360,(80,180,255),2)
        cv2.circle(rc,(ecx,ecy),2,(255,255,255),-1)
    return len(valid)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — OBJECT DETECTOR (phone / earphone)
# ══════════════════════════════════════════════════════════════════════════════
class ObjectDetector:
    def __init__(self, sid):
        self.sid=sid
        self.phone_since=None; self.phone_fired=False
        self.ear_since=None; self.ear_fired=False

    def run(self, frame, face_boxes):
        if not YOLO_ENABLED: return frame
        h,w = frame.shape[:2]
        now = time.time()
        results = _yolo_model.predict(
            frame,
            classes=[67],       # COCO class 67 = cell phone
            conf=0.08,          # detects smaller/distant phones
            imgsz=960,
            verbose=False
        )[0]

        phone_seen=False; earphone_seen=False

        for box in results.boxes:
            cls_id=int(box.cls[0]); conf=float(box.conf[0])
            x1,y1,x2,y2=map(int,box.xyxy[0])

            if cls_id == _PHONE_CLASS_ID:
                phone_seen=True
                cv2.rectangle(frame,(x1,y1),(x2,y2),_COL_PHONE,2)
                _label(frame,f"PHONE {conf:.0%}",(x1,y1-6),color=(255,255,255),bg=_COL_PHONE)
            elif face_boxes:
                obj_area=(x2-x1)*(y2-y1); frame_area=w*h
                if obj_area < frame_area*0.08:
                    ocx,ocy=(x1+x2)//2,(y1+y2)//2
                    for (fx,fy,fw,fh) in face_boxes:
                        ey_top=fy+int(fh*0.20); ey_bot=fy+int(fh*0.60)
                        margin=int(fw*0.35)
                        near_l=abs(ocx-fx)<margin and ey_top<ocy<ey_bot
                        near_r=abs(ocx-(fx+fw))<margin and ey_top<ocy<ey_bot
                        if near_l or near_r:
                            earphone_seen=True
                            cv2.rectangle(frame,(x1,y1),(x2,y2),_COL_EARPHONE,2)
                            _label(frame,f"EARPHONE? {conf:.0%}",(x1,y1-6),color=(255,255,255),bg=_COL_EARPHONE)
                            break

        if phone_seen:
            if self.phone_since is None: self.phone_since=now; self.phone_fired=False
            el=now-self.phone_since
            bw=int(w*0.3*min(el/OBJECT_ALERT_SECS,1.0))
            cv2.rectangle(frame,(0,h-6),(bw,h),_COL_PHONE,-1)
            rem=max(0,OBJECT_ALERT_SECS-int(el))
            _label(frame,f"PHONE — logging in {rem}s" if rem>0 else "PHONE — LOGGED",(6,h-10),scale=0.44,bg=_COL_PHONE)
            if el>=OBJECT_ALERT_SECS and not self.phone_fired:
                _add_violation(self.sid,"PHONE_DETECTED","Mobile phone visible for 3+ seconds")
                self.phone_fired=True
        else:
            self.phone_since=None; self.phone_fired=False

        if earphone_seen:
            if self.ear_since is None: self.ear_since=now; self.ear_fired=False
            el=now-self.ear_since
            bw=int(w*0.3*min(el/OBJECT_ALERT_SECS,1.0))
            cv2.rectangle(frame,(0,h-12),(bw,h-6),_COL_EARPHONE,-1)
            rem=max(0,OBJECT_ALERT_SECS-int(el))
            _label(frame,f"EARPHONE? — logging in {rem}s" if rem>0 else "EARPHONE — LOGGED",(6,h-24),scale=0.44,bg=_COL_EARPHONE)
            if el>=OBJECT_ALERT_SECS and not self.ear_fired:
                _add_violation(self.sid,"EARPHONE_DETECTED","Possible earphone near ear for 3+ seconds")
                self.ear_fired=True
        else:
            self.ear_since=None; self.ear_fired=False

        return frame

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — PER-STUDENT STATE
# ══════════════════════════════════════════════════════════════════════════════
def _make_student_state(sid):
    return {
        "id": sid, "name": STUDENTS[sid]["name"], "online": False,
        "num_faces":0, "num_eyes":0, "fps":0.0, "direction":"Center",
        "total_frames":0, "detected":0, "absent":0, "multi":0,
        "face_absent_secs":0, "multi_face_secs":0, "detection_rate":0.0,
        "violations":[], "jpeg_frame":None, "start_time":time.time(), "elapsed":"00:00",
        "_face_stab":Stabiliser(10), "_eye_stab":Stabiliser(6),
        "_absent_since":None, "_absent_fired":False,
        "_multi_since":None, "_multi_fired":False,
        "_prev_time":time.time(), "_obj_detector":None,
    }

student_locks  = {sid: threading.Lock() for sid in STUDENTS}
student_states = {sid: _make_student_state(sid) for sid in STUDENTS}

def _init_object_detectors():
    for sid in STUDENTS:
        student_states[sid]["_obj_detector"] = ObjectDetector(sid)

_global_lock = threading.Lock()
global_violations = []

def _add_violation(sid, vtype, detail):
    ts=time.strftime("%H:%M:%S")
    entry={"type":vtype,"time":ts,"detail":detail,"student_id":sid,"student_name":STUDENTS[sid]["name"]}
    with student_locks[sid]:
        student_states[sid]["violations"].append(entry)
    with _global_lock:
        global_violations.append(entry)
    print(f"[VIOLATION] {ts}  {STUDENTS[sid]['name']}  {vtype}  —  {detail}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7B — LOCAL IP
# ══════════════════════════════════════════════════════════════════════════════
def get_local_ip():
    try:
        s=_socket.socket(_socket.AF_INET,_socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"
LOCAL_IP = get_local_ip()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7C — BROWSER FRAME PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════
def process_browser_frame(sid, jpeg_bytes):
    st=student_states[sid]; lk=student_locks[sid]
    arr=_np.frombuffer(jpeg_bytes,dtype='uint8')
    frame=cv2.imdecode(arr,cv2.IMREAD_COLOR)
    if frame is None: return

    frame=cv2.flip(frame,1)
    h,w=frame.shape[:2]
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    gray=cv2.equalizeHist(gray)

    raw_faces=face_cascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=8,
        minSize=(70,70),flags=cv2.CASCADE_SCALE_IMAGE)
    stable_n=st["_face_stab"].update(len(raw_faces))
    now_t=time.time()

    if stable_n==0:
        if st["_absent_since"] is None: st["_absent_since"]=now_t; st["_absent_fired"]=False
        if (now_t-st["_absent_since"])>=ABSENT_ALERT_SECS and not st["_absent_fired"]:
            _add_violation(sid,"FACE_ABSENT",f"No face for {ABSENT_ALERT_SECS}s")
            st["_absent_fired"]=True
    else:
        st["_absent_since"]=None; st["_absent_fired"]=False

    if stable_n>1:
        if st["_multi_since"] is None: st["_multi_since"]=now_t; st["_multi_fired"]=False
        if (now_t-st["_multi_since"])>=MULTI_ALERT_SECS and not st["_multi_fired"]:
            _add_violation(sid,"MULTIPLE_FACES",f"{stable_n} faces for {MULTI_ALERT_SECS}s")
            st["_multi_fired"]=True
    else:
        st["_multi_since"]=None; st["_multi_fired"]=False

    absent_secs=int(now_t-st["_absent_since"]) if st["_absent_since"] else 0
    multi_secs=int(now_t-st["_multi_since"]) if st["_multi_since"] else 0

    raw_eyes=0
    for idx,(fx,fy,fw,fh) in enumerate(raw_faces):
        col=(0,220,80) if stable_n<=1 else (0,150,255)
        if idx==0: raw_eyes=_detect_eyes(gray,frame,fx,fy,fw,fh)
        _corner_rect(frame,(fx,fy,fw,fh),col)
        _label(frame,f"S{sid+1}-F{idx+1}",(fx,fy-5),color=col,bg=(0,40,15))
        cv2.circle(frame,(fx+fw//2,fy+fh//2),3,col,-1)

    stable_eyes=st["_eye_stab"].update(raw_eyes)

    face_list=[(fx,fy,fw,fh) for (fx,fy,fw,fh) in raw_faces]
    frame=st["_obj_detector"].run(frame,face_list)

    prev=st.get("_prev_time",now_t)
    fps=round(1.0/max(now_t-prev,1e-6),1)
    st["_prev_time"]=now_t

    with lk: vc=len(st["violations"])
    _status_banner(frame,stable_n,STUDENTS[sid]["name"],w)
    _hud(frame,fps,stable_n,stable_eyes,"Browser",w,h,vc)

    ok,buf=cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,78])
    elapsed=int(now_t-st["start_time"]); m,s2=divmod(elapsed,60)
    total=max(st["total_frames"],1)

    if ok:
        with lk:
            st["jpeg_frame"]=buf.tobytes()
            st["online"]=True
            st["num_faces"]=stable_n
            st["num_eyes"]=stable_eyes
            st["fps"]=fps
            st["face_absent_secs"]=absent_secs
            st["multi_face_secs"]=multi_secs
            st["elapsed"]=f"{m:02d}:{s2:02d}"
            st["total_frames"]+=1
            st["detection_rate"]=round(st["detected"]/total*100,1)
            if stable_n==0: st["absent"]+=1
            elif stable_n==1: st["detected"]+=1
            else: st["detected"]+=1; st["multi"]+=1

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — USB CAMERA THREAD
# ══════════════════════════════════════════════════════════════════════════════
def camera_thread(sid):
    src=STUDENTS[sid]["src"]; name=STUDENTS[sid]["name"]
    if src=="browser":
        print(f"[CAM-{sid}] {name} — browser mode. Waiting for /join/{sid} connection...")
        return

    st=student_states[sid]; lk=student_locks[sid]

    # ── Open camera with Windows-safe backend ──────────────────────────────────
    # cv2.CAP_MSMF (the default on Windows) frequently throws
    # "OnReadSample() error -1072875772" right after opening — this is a known
    # Windows Media Foundation issue, especially with certain webcam drivers.
    # cv2.CAP_DSHOW (DirectShow) is far more reliable on Windows.
    if os.name == "nt" and isinstance(src, int):
        cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(src)

    if not cap.isOpened():
        print(f"[CAM-{sid}] Cannot open source: {src}"); return

    # Force a fixed resolution — some webcams fail to grab frames until
    # a resolution is explicitly set on Windows.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # reduces latency, helps some drivers

    # ── Warm-up: retry reading the first frame a few times ─────────────────────
    # Many webcams need a short delay before the sensor actually starts
    # streaming; the very first read() can legitimately fail.
    test = None
    for attempt in range(10):
        ret, test = cap.read()
        if ret and test is not None:
            break
        print(f"[CAM-{sid}] Warm-up attempt {attempt+1}/10 failed, retrying...")
        time.sleep(0.3)
    else:
        print(f"[CAM-{sid}] Cannot read first frame after 10 attempts.")
        print(f"[CAM-{sid}] Fix: close other apps using the camera (Zoom/Teams/browser),")
        print(f"[CAM-{sid}]      or try a different index in STUDENTS[{sid}]['src'].")
        cap.release(); return

    h,w=test.shape[:2]
    with lk: st["online"]=True

    face_stab=Stabiliser(10); eye_stab=Stabiliser(6); tracker=MovementTracker()
    prev_time=time.time()
    absent_since=None; absent_fired=False
    multi_since=None; multi_fired=False
    consecutive_fail=0

    print(f"[CAM-{sid}] {name} started — {w}x{h} from {src}")

    while True:
        ret,frame=cap.read()
        if not ret:
            consecutive_fail += 1
            # If the camera drops out for too long, try to reopen it
            if consecutive_fail >= 60:   # ~3 seconds of failures
                print(f"[CAM-{sid}] Camera stalled — attempting to reopen...")
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(src, cv2.CAP_DSHOW) if (os.name=="nt" and isinstance(src,int)) else cv2.VideoCapture(src)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                consecutive_fail = 0
                with lk: st["online"] = cap.isOpened()
            time.sleep(0.05); continue
        consecutive_fail = 0

        frame=cv2.flip(frame,1)
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        gray=cv2.equalizeHist(gray)

        raw_faces=face_cascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=8,
            minSize=(70,70),flags=cv2.CASCADE_SCALE_IMAGE)
        stable_n=face_stab.update(len(raw_faces))
        now_t=time.time()

        if stable_n==0:
            if absent_since is None: absent_since=now_t; absent_fired=False
            if (now_t-absent_since)>=ABSENT_ALERT_SECS and not absent_fired:
                _add_violation(sid,"FACE_ABSENT",f"No face for {ABSENT_ALERT_SECS}s")
                absent_fired=True
        else:
            absent_since=None; absent_fired=False

        if stable_n>1:
            if multi_since is None: multi_since=now_t; multi_fired=False
            if (now_t-multi_since)>=MULTI_ALERT_SECS and not multi_fired:
                _add_violation(sid,"MULTIPLE_FACES",f"{stable_n} faces for {MULTI_ALERT_SECS}s")
                multi_fired=True
        else:
            multi_since=None; multi_fired=False

        absent_secs=int(now_t-absent_since) if absent_since else 0
        multi_secs=int(now_t-multi_since) if multi_since else 0

        raw_eyes=0
        for idx,(fx,fy,fw,fh) in enumerate(raw_faces):
            cx,cy=fx+fw//2,fy+fh//2
            col=(0,220,80) if stable_n<=1 else (0,150,255)
            if idx==0:
                tracker.update(cx,cy)
                raw_eyes=_detect_eyes(gray,frame,fx,fy,fw,fh)
            _corner_rect(frame,(fx,fy,fw,fh),col)
            _label(frame,f"S{sid+1}-F{idx+1}",(fx,fy-5),color=col,bg=(0,40,15))
            cv2.circle(frame,(cx,cy),3,col,-1)

        if stable_n==0: tracker.reset()

        stable_eyes=eye_stab.update(raw_eyes)

        face_list=[(fx,fy,fw,fh) for (fx,fy,fw,fh) in raw_faces]
        frame=st["_obj_detector"].run(frame,face_list)

        tracker.draw_trail(frame)
        direction=tracker.direction
        if any(k in direction for k in ("Left","Right","Up","Down")):
            ax,ay=w-50,50
            for k,(ddx,ddy) in {"Left":(-25,0),"Right":(25,0),"Up":(0,-25),"Down":(0,25)}.items():
                if k in direction:
                    cv2.arrowedLine(frame,(ax,ay),(ax+ddx,ay+ddy),(255,200,80),2,tipLength=0.4)

        now=time.time(); fps=1.0/max(now-prev_time,1e-6); prev_time=now

        with lk: vc=len(st["violations"])
        _status_banner(frame,stable_n,name,w)
        _hud(frame,fps,stable_n,stable_eyes,direction,w,h,vc)

        elapsed=int(now-st["start_time"]); m,s=divmod(elapsed,60)
        total=max(st["total_frames"],1)
        with lk:
            st["num_faces"]=stable_n
            st["num_eyes"]=stable_eyes
            st["fps"]=round(fps,1)
            st["direction"]=direction
            st["total_frames"]+=1
            st["face_absent_secs"]=absent_secs
            st["multi_face_secs"]=multi_secs
            st["elapsed"]=f"{m:02d}:{s:02d}"
            st["detection_rate"]=round(st["detected"]/total*100,1)
            if stable_n==0: st["absent"]+=1
            elif stable_n==1: st["detected"]+=1
            else: st["detected"]+=1; st["multi"]+=1

        ok,buf=cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,78])
        if ok:
            with lk: st["jpeg_frame"]=buf.tobytes()

        time.sleep(0.01)

    cap.release()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — THREADED HTTP SERVER
# ══════════════════════════════════════════════════════════════════════════════
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads=True

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — EXAM LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
def get_exam_for_api(sid=None):
    """Returns the exam JSON. Same exam for every student — no scheduling."""
    return EXAM

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — HTTP HANDLER
# ══════════════════════════════════════════════════════════════════════════════
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a): pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        path=urlparse(self.path).path
        parts=[p for p in path.split("/") if p]

        if path in ("/","/dashboard"):
            return self._file("dashboard.html","text/html")

        if len(parts)==2 and parts[0]=="join":
            sid=self._sid(parts[1])
            if sid is None: return self.send_error(404)
            return self._serve_join_page(sid)

        if len(parts)==2 and parts[0]=="exam":
            sid=self._sid(parts[1])
            if sid is None: return self.send_error(404)
            return self._file("exam.html","text/html")

        if len(parts)==2 and parts[0]=="stream":
            sid=self._sid(parts[1])
            if sid is None: return self.send_error(404)
            return self._stream(sid)

        if path=="/api/status":
            return self._status()

        if path=="/api/exam":
            return self._json(get_exam_for_api())

        if len(parts)==3 and parts[0]=="api" and parts[1]=="exam":
            sid=self._sid(parts[2])
            if sid is None: return self.send_error(404)
            return self._json(get_exam_for_api(sid))

        self.send_error(404)

    def do_POST(self):
        path=urlparse(self.path).path
        parts=[p for p in path.split("/") if p]

        if len(parts)==3 and parts[0]=="api" and parts[1]=="event":
            sid=self._sid(parts[2])
            if sid is None: return self.send_error(404)
            return self._event(sid)

        if len(parts)==2 and parts[0]=="browser_frame":
            sid=self._sid(parts[1])
            if sid is None: return self.send_error(404)
            return self._receive_browser_frame(sid)

        if len(parts)==3 and parts[0]=="api" and parts[1]=="submit":
            sid=self._sid(parts[2])
            if sid is None: return self.send_error(404)
            return self._submit(sid)

        self.send_error(404)

    def _stream(self,sid):
        self.send_response(200); self._cors()
        self.send_header("Content-Type","multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control","no-cache")
        self.end_headers()
        lk=student_locks[sid]; st=student_states[sid]
        try:
            while True:
                with lk: jpg=st["jpeg_frame"]
                if jpg:
                    try:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "+
                            str(len(jpg)).encode()+b"\r\n\r\n"+jpg+b"\r\n")
                        self.wfile.flush()
                    except: break
                time.sleep(0.033)
        except (BrokenPipeError,ConnectionResetError,OSError): pass

    def _status(self):
        students_out=[]
        for sid in STUDENTS:
            with student_locks[sid]:
                s=student_states[sid]
                students_out.append({
                    "id":s["id"],"name":s["name"],"online":s["online"],
                    "num_faces":s["num_faces"],"num_eyes":s["num_eyes"],"fps":s["fps"],
                    "direction":s["direction"],"total_frames":s["total_frames"],
                    "detected":s["detected"],"absent":s["absent"],"multi":s["multi"],
                    "detection_rate":s["detection_rate"],
                    "face_absent_secs":s["face_absent_secs"],
                    "multi_face_secs":s["multi_face_secs"],
                    "elapsed":s["elapsed"],"violation_count":len(s["violations"]),
                })
        with _global_lock: gv=list(global_violations)
        self._json({"students":students_out,"global_violations":gv[-40:],"total_violations":len(gv)})

    def _event(self,sid):
        try:
            length=int(self.headers.get("Content-Length",0))
            data=json.loads(self.rfile.read(length))
            vtype=data.get("type","UNKNOWN"); detail=data.get("detail","")
            _add_violation(sid,vtype,detail)
            self._json({"ok":True})
        except Exception as e:
            self._json({"ok":False,"error":str(e)},400)

    def _receive_browser_frame(self,sid):
        try:
            length=int(self.headers.get("Content-Length",0))
            data=self.rfile.read(length)
            if not hasattr(self.server, "processing_students"):
                self.server.processing_students = set()

            if sid not in self.server.processing_students:
                self.server.processing_students.add(sid)

                def process_one_frame():
                    try:
                        process_browser_frame(sid, data)
                    finally:
                        self.server.processing_students.discard(sid)

            threading.Thread(target=process_one_frame, daemon=True).start().start()
            self.send_response(200); self._cors()
            self.send_header("Content-Length","2"); self.end_headers()
            self.wfile.write(b"ok")
        except Exception as e:
            self.send_error(500,str(e))

    def _submit(self,sid):
        try:
            length=int(self.headers.get("Content-Length",0))
            data=json.loads(self.rfile.read(length))
            exam_id=data.get("exam_id"); answers=data.get("answers",[])
            with student_locks[sid]: vcount=len(student_states[sid]["violations"])
            name=STUDENTS[sid]["name"]

            # Auto-score against EXAM's correct answers
            score=0
            for i,q in enumerate(EXAM["questions"]):
                given = answers[i] if i < len(answers) else None
                if given == q.get("correct"):
                    score += q["marks"]

            entry = {
                "id": f"sub-{sid}-{int(time.time())}",
                "exam_id": exam_id,
                "student_id": sid,
                "student_name": name,
                "answers": answers,
                "score": score,
                "total_marks": EXAM["total_marks"],
                "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "violation_count": vcount,
            }
            with _submissions_lock:
                submissions.append(entry)

            print(f"[SUBMIT] {name} submitted — score {score}/{EXAM['total_marks']} — {vcount} violations")
            self._json({"ok":True,"submission_id":entry["id"],"score":score,"total_marks":EXAM["total_marks"]})
        except Exception as e:
            self._json({"ok":False,"error":str(e)},400)

    def _sid(self,s):
        try:
            sid=int(s); return sid if sid in STUDENTS else None
        except: return None

    def _file(self,name,mime):
        try:
            data=open(name,"rb").read()
            self.send_response(200); self._cors()
            self.send_header("Content-Type",mime)
            self.send_header("Content-Length",len(data))
            self.end_headers(); self.wfile.write(data)
        except FileNotFoundError:
            self.send_error(404,f"{name} not found")

    def _json(self,payload,code=200):
        data=json.dumps(payload).encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",len(data))
        self.end_headers(); self.wfile.write(data)

    # ── GET /join/<id> — self-contained browser camera + exam page ────────────
    def _serve_join_page(self, sid):
        name=STUDENTS[sid]["name"]
        host=self.headers.get("Host", f"{LOCAL_IP}:5000")
        server_url=f"http://{host}"

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ProctorScope — {name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#eef1f5;--white:#fff;--s1:#f7f8fa;--bd:#dde1e7;--bd2:#c8cdd6;--ink:#1a1d23;--ink2:#3d4250;--ink3:#6b7080;--blue:#1565c0;--blue2:#1976d2;--blue3:#e3f0ff;--green:#2e7d32;--green2:#4caf50;--red:#c62828;--ora:#e65100;--grey2:#f0f0f0;--mono:'JetBrains Mono',monospace;--sans:'Inter',sans-serif}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:var(--sans);background:var(--bg);color:var(--ink);height:100vh;display:flex;flex-direction:column;overflow:hidden}}
#wov{{display:none;position:fixed;inset:0;z-index:900;align-items:center;justify-content:center;background:rgba(198,40,40,.15);backdrop-filter:blur(4px)}}
#wov.show{{display:flex}}
.wcard{{background:#fff;border-radius:10px;padding:32px 40px;max-width:400px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.25);border-top:5px solid var(--red)}}
.wnum{{font-family:var(--mono);font-size:2.1rem;font-weight:700;color:var(--red)}}
.wlbl{{font-size:.6rem;font-weight:600;letter-spacing:.08em;color:var(--ink3);text-transform:uppercase;margin-bottom:10px}}
.wtit{{font-size:1.1rem;font-weight:700;color:var(--red);margin-bottom:6px}}
.wbod{{font-size:.82rem;color:var(--ink3);line-height:1.6;margin-bottom:18px}}
.wbtn{{font-size:.72rem;font-weight:600;padding:9px 22px;background:var(--red);color:#fff;border:none;border-radius:6px;cursor:pointer}}
#scov{{display:none;position:fixed;inset:0;z-index:950;align-items:center;justify-content:center;background:rgba(0,0,0,.4)}}
#scov.show{{display:flex}}
.sccard{{background:#fff;border-radius:10px;padding:26px 30px;max-width:360px;box-shadow:0 20px 60px rgba(0,0,0,.25)}}
.sctit{{font-size:1rem;font-weight:700;margin-bottom:8px}}
.scbod{{font-size:.8rem;color:var(--ink3);line-height:1.6;margin-bottom:18px}}
.scbtns{{display:flex;gap:10px;justify-content:flex-end}}
.scbtn{{font-size:.72rem;font-weight:600;padding:8px 18px;border-radius:6px;border:1px solid var(--bd2);background:#fff;cursor:pointer}}
.scbtn.yes{{background:var(--blue);color:#fff;border-color:var(--blue)}}
.header{{background:var(--blue);color:#fff;height:50px;display:flex;align-items:center;justify-content:space-between;padding:0 18px;flex-shrink:0}}
.h-brand{{font-weight:700;font-size:.8rem}}
.h-exam{{font-size:.68rem;opacity:.8}}
.timer-box{{background:rgba(255,255,255,.15);padding:5px 14px;border-radius:6px;font-family:var(--mono);font-weight:600}}
.timer-box.warn{{background:rgba(255,80,80,.4)}}
.stu-tag{{font-size:.65rem;background:rgba(255,255,255,.15);padding:4px 10px;border-radius:5px;margin-right:10px}}
.cam-strip{{background:var(--ink);color:#fff;height:32px;display:flex;align-items:center;padding:0 18px;gap:12px;flex-shrink:0;font-size:.66rem}}
.cam-dot{{width:7px;height:7px;border-radius:50%;background:#666}}
.cam-dot.ok{{background:var(--green2)}}
.cam-dot.err{{background:var(--red)}}
main{{flex:1;display:grid;grid-template-columns:1fr 230px;overflow:hidden}}
.qarea{{overflow-y:auto;padding:20px 26px}}
.qmeta-bar{{display:flex;justify-content:space-between;margin-bottom:14px;padding-bottom:10px;border-bottom:2px solid var(--bd2);font-size:.76rem;color:var(--ink3)}}
.qmarks-tag{{font-family:var(--mono);font-size:.64rem;background:var(--blue3);color:var(--blue);padding:3px 9px;border-radius:5px;font-weight:600}}
.qcard{{background:#fff;border:1px solid var(--bd);border-radius:10px;padding:22px 24px}}
.qnum-lbl{{font-size:.66rem;font-weight:700;color:var(--blue);text-transform:uppercase;margin-bottom:9px}}
.qtext{{font-size:.95rem;line-height:1.65;margin-bottom:18px}}
.opts{{display:flex;flex-direction:column;gap:9px}}
.opt{{display:flex;align-items:center;gap:11px;padding:11px 14px;border:1.5px solid var(--bd);border-radius:8px;cursor:pointer;background:var(--s1)}}
.opt.sel{{border-color:var(--blue);background:var(--blue3)}}
.opt-radio{{width:17px;height:17px;accent-color:var(--blue)}}
.opt-txt{{font-size:.84rem;color:var(--ink2)}}
.opt.sel .opt-txt{{color:var(--ink);font-weight:500}}
.nav-row{{display:flex;justify-content:space-between;margin-top:18px;gap:8px}}
.nav-left,.nav-right{{display:flex;gap:8px}}
.nbtn{{font-size:.74rem;font-weight:600;padding:9px 18px;border-radius:6px;border:1px solid var(--bd2);background:#fff;cursor:pointer;color:var(--ink2)}}
.nbtn:disabled{{opacity:.35}}
.nbtn.mark{{border-color:var(--ora);color:var(--ora)}}
.nbtn.next{{background:var(--blue);color:#fff;border-color:var(--blue)}}
.nbtn.submit{{background:var(--green);color:#fff;border-color:var(--green)}}
.sidebar{{background:#fff;border-left:1px solid var(--bd);display:flex;flex-direction:column;overflow:hidden}}
.sb-section{{padding:12px 14px;border-bottom:1px solid var(--bd)}}
.sb-title{{font-size:.62rem;font-weight:700;text-transform:uppercase;color:var(--ink3);margin-bottom:8px}}
.legend{{display:flex;flex-direction:column;gap:5px}}
.leg-item{{display:flex;align-items:center;gap:7px;font-size:.62rem;color:var(--ink2)}}
.leg-dot{{width:11px;height:11px;border-radius:3px}}
.leg-answered{{background:var(--green2)}}
.leg-notans{{background:var(--grey2);border:1px solid var(--bd2)}}
.leg-review{{background:var(--ora)}}
.leg-notvisited{{background:#fff;border:1px solid var(--bd2)}}
.qgrid-wrap{{flex:1;overflow-y:auto;padding:12px 14px}}
.qgrid{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}}
.qnum-btn{{aspect-ratio:1;border-radius:5px;border:1.5px solid var(--bd2);background:#fff;font-family:var(--mono);font-size:.7rem;font-weight:600;cursor:pointer;color:var(--ink2)}}
.qnum-btn.answered{{background:var(--green2);border-color:var(--green2);color:#fff}}
.qnum-btn.review{{background:var(--ora);border-color:var(--ora);color:#fff}}
.qnum-btn.current{{outline:2px solid var(--blue)}}
.submit-btn-wrap{{padding:12px 14px;border-top:1px solid var(--bd)}}
.big-submit{{width:100%;padding:11px;background:var(--green);color:#fff;border:none;border-radius:6px;font-weight:700;font-size:.8rem;cursor:pointer}}
</style></head><body>

<div id="wov"><div class="wcard">
  <div class="wnum" id="wnum">1</div>
  <div class="wlbl">Violation Recorded</div>
  <div class="wtit" id="wtit">Tab Switch Detected</div>
  <div class="wbod" id="wbod">You navigated away. This has been reported to your proctor.</div>
  <button class="wbtn" onclick="dismissW()">Return to Exam</button>
</div></div>

<div id="scov"><div class="sccard">
  <div class="sctit">Submit Exam?</div>
  <div class="scbod">Answered <b id="sc-ans">0</b> of <b id="sc-total">0</b> questions.</div>
  <div class="scbtns"><button class="scbtn" onclick="closeSC()">Cancel</button><button class="scbtn yes" onclick="doSubmit()">Yes, Submit</button></div>
</div></div>

<div class="header">
  <div><div class="h-brand">PROCTORSCOPE</div><div class="h-exam" id="h-exam-title">Loading exam...</div></div>
  <div style="display:flex;align-items:center">
    <div class="stu-tag">STUDENT {sid+1}</div>
    <div class="timer-box" id="timer">45:00</div>
  </div>
</div>

<div class="cam-strip">
  <div class="cam-dot" id="cdot"></div>
  <div id="clab">Camera connecting...</div>
</div>

<main>
  <div class="qarea" id="qarea"><div style="text-align:center;padding:60px;color:var(--ink3)">Loading exam...</div></div>
  <div class="sidebar">
    <div class="sb-section">
      <div class="sb-title">Legend</div>
      <div class="legend">
        <div class="leg-item"><div class="leg-dot leg-answered"></div>Answered</div>
        <div class="leg-item"><div class="leg-dot leg-notvisited"></div>Not Visited</div>
        <div class="leg-item"><div class="leg-dot leg-review"></div>Marked for Review</div>
      </div>
    </div>
    <div class="qgrid-wrap"><div class="sb-title">Questions</div><div class="qgrid" id="qgrid"></div></div>
    <div class="submit-btn-wrap"><button class="big-submit" onclick="openSC()">Save &amp; Finish</button></div>
  </div>
</main>

<canvas id="c" style="display:none"></canvas>
<video id="v" autoplay playsinline muted style="display:none"></video>

<script>
const SID={sid};
const SERVER='{server_url}';
let questions=[],answers=[],marked=[],visited=[],curQ=0,currentExamId=null;
let secsLeft=2700,loaded=false,submitted=false,viols=0,wActive=false,streaming=false;

async function startCamera(){{
  try{{
    const stream=await navigator.mediaDevices.getUserMedia({{video:{{width:640,height:480,facingMode:'user'}},audio:false}});
    const vid=document.getElementById('v'); vid.srcObject=stream;
    vid.onloadedmetadata=()=>{{
      document.getElementById('c').width=vid.videoWidth;
      document.getElementById('c').height=vid.videoHeight;
      document.getElementById('cdot').className='cam-dot ok';
      document.getElementById('clab').textContent='Camera streaming to proctor';
      streaming=true; sendFrame();
    }};
  }}catch(e){{
    document.getElementById('cdot').className='cam-dot err';
    document.getElementById('clab').textContent='Camera denied: '+e.message;
  }}
}}

async function sendFrame(){{
  if(!streaming) return;
  const vid=document.getElementById('v'),c=document.getElementById('c'),ctx=c.getContext('2d');
  ctx.drawImage(vid,0,0,c.width,c.height);
  c.toBlob(async blob=>{{
    if(blob){{
      try{{ await fetch(SERVER+'/browser_frame/'+SID,{{method:'POST',headers:{{'Content-Type':'image/jpeg'}},body:blob,keepalive:true}}); }}catch(e){{}}
    }}
    setTimeout(sendFrame,600);
  }},'image/jpeg',0.75);
}}

async function loadExam(){{
  try{{
    const d=await(await fetch(SERVER+'/api/exam/'+SID)).json();
    currentExamId=d.id||null;
    questions=d.questions||[]; answers=new Array(questions.length).fill(null);
    marked=new Array(questions.length).fill(false); visited=new Array(questions.length).fill(false);
    secsLeft=(d.duration_minutes||45)*60;
    document.getElementById('h-exam-title').textContent=d.title||'Examination';
    buildGrid(); renderQ(); loaded=true;
  }}catch(e){{ setTimeout(loadExam,4000); }}
}}

function buildGrid(){{
  const g=document.getElementById('qgrid');
  g.innerHTML=questions.map((_,i)=>{{
    let cls='qnum-btn';
    if(i===curQ) cls+=' current';
    else if(marked[i]) cls+=' review';
    else if(answers[i]!==null) cls+=' answered';
    return '<button class="'+cls+'" onclick="jumpTo('+i+')">'+(i+1)+'</button>';
  }}).join('');
}}

function jumpTo(i){{curQ=i;renderQ();}}

function renderQ(){{
  if(!questions.length)return;
  visited[curQ]=true;
  const q=questions[curQ]; const L=['A','B','C','D']; const isLast=curQ===questions.length-1;
  document.getElementById('qarea').innerHTML=
    '<div class="qmeta-bar"><div>Question <b>'+(curQ+1)+'</b> of <b>'+questions.length+'</b></div>'+
    '<div class="qmarks-tag">'+q.marks+' Mark'+(q.marks>1?'s':'')+'</div></div>'+
    '<div class="qcard"><div class="qnum-lbl">Question '+(curQ+1)+'</div><div class="qtext">'+q.text+'</div>'+
    '<div class="opts">'+q.options.map((o,i)=>
      '<div class="opt'+(answers[curQ]===i?' sel':'')+'" onclick="selOpt('+i+')">'+
      '<input type="radio" class="opt-radio" '+(answers[curQ]===i?'checked':'')+' readonly>'+
      '<div class="opt-txt"><b>'+L[i]+'.</b> '+o+'</div></div>').join('')+'</div></div>'+
    '<div class="nav-row"><div class="nav-left">'+
    '<button class="nbtn" onclick="prevQ()" '+(curQ===0?'disabled':'')+'>← Previous</button>'+
    '<button class="nbtn" onclick="answers[curQ]=null;renderQ()">Clear</button></div>'+
    '<div class="nav-right"><button class="nbtn mark" onclick="marked[curQ]=!marked[curQ];renderQ()">'+(marked[curQ]?'✓ Marked':'🚩 Review')+'</button>'+
    '<button class="nbtn '+(isLast?'submit':'next')+'" onclick="'+(isLast?'openSC()':'nextQ()')+'">'+(isLast?'Save & Finish':'Save & Next →')+'</button></div></div>';
  buildGrid();
}}

function selOpt(i){{answers[curQ]=i;renderQ();}}
function nextQ(){{if(curQ<questions.length-1){{curQ++;renderQ();}}}}
function prevQ(){{if(curQ>0){{curQ--;renderQ();}}}}

setInterval(()=>{{
  if(!loaded||submitted)return;
  secsLeft=Math.max(0,secsLeft-1);
  const m=String(Math.floor(secsLeft/60)).padStart(2,'0'),s=String(secsLeft%60).padStart(2,'0');
  const el=document.getElementById('timer'); el.textContent=m+':'+s;
  if(secsLeft<=300) el.classList.add('warn');
  if(secsLeft===0) doSubmit();
}},1000);

function openSC(){{
  const ans=answers.filter(a=>a!==null).length;
  document.getElementById('sc-ans').textContent=ans;
  document.getElementById('sc-total').textContent=questions.length;
  document.getElementById('scov').classList.add('show');
}}
function closeSC(){{document.getElementById('scov').classList.remove('show');}}

async function doSubmit(){{
  if(submitted)return; submitted=true; closeSC();
  try{{
    const res=await fetch(SERVER+'/api/submit/'+SID,{{method:'POST',headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{exam_id:currentExamId,answers}})}});
    const result=await res.json();
    const ans=answers.filter(a=>a!==null).length;
    if(result.ok){{
      document.getElementById('qarea').innerHTML='<div style="text-align:center;padding:80px 20px">'+
        '<div style="font-size:2.2rem;margin-bottom:14px">✓</div>'+
        '<div style="font-size:1.15rem;font-weight:700;margin-bottom:8px">Paper Submitted Successfully</div>'+
        '<div style="font-size:.8rem;color:var(--ink3);line-height:2">Answered '+ans+' of '+questions.length+' questions<br>'+
        viols+' violation'+(viols!==1?'s':'')+' recorded</div></div>';
      document.querySelector('.sidebar').style.display='none';
    }}
  }}catch(e){{ submitted=false; alert('Could not submit — check connection.'); }}
}}

async function postViol(type,detail){{
  const payload=JSON.stringify({{type,detail}});
  try{{ await fetch(SERVER+'/api/event/'+SID,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:payload,keepalive:true}}); }}catch(e){{}}
  try{{ navigator.sendBeacon(SERVER+'/api/event/'+SID,new Blob([payload],{{type:'application/json'}})); }}catch(e){{}}
}}
function logViol(type,detail){{ viols++; postViol(type,detail); }}
function showWarn(title,body){{
  if(wActive)return; wActive=true;
  document.getElementById('wnum').textContent=viols;
  document.getElementById('wtit').textContent=title;
  document.getElementById('wbod').textContent=body;
  document.getElementById('wov').classList.add('show');
}}
function dismissW(){{wActive=false;document.getElementById('wov').classList.remove('show');}}

document.addEventListener('visibilitychange',()=>{{
  if(document.visibilityState==='hidden'){{ logViol('TAB_SWITCH','Candidate switched away from exam tab'); }}
  else{{ logViol('WINDOW_FOCUS','Candidate returned to exam tab'); showWarn('Tab Switch Detected','You navigated away. This has been reported to your proctor.'); }}
}});
window.addEventListener('blur',()=>{{
  if(document.visibilityState==='visible'){{ logViol('WINDOW_BLUR','Browser window lost focus'); showWarn('Window Focus Lost','You switched to another app. This has been logged.'); }}
}});

startCamera();
loadExam();
</script></body></html>"""

        body=html.encode()
        self.send_response(200); self._cors()
        self.send_header("Content-Type","text/html")
        self.send_header("Content-Length",len(body))
        self.end_headers(); self.wfile.write(body)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 12 — ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    _init_object_detectors()

    for sid in STUDENTS:
        threading.Thread(target=camera_thread, args=(sid,), daemon=True).start()

    PORT = 5000
    server = ThreadingHTTPServer(("", PORT), Handler)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║      ProctorScope  —  4-Student Mode  +  Exam System     ║
╠══════════════════════════════════════════════════════════╣
║  Proctor Dashboard → http://localhost:{PORT}                 ║
╠══════════════════════════════════════════════════════════╣
║  Student 1 (USB)     → http://localhost:{PORT}/exam/0        ║
║  Student 2 (browser) → http://{LOCAL_IP}:{PORT}/join/1  ║
║  Student 3 (browser) → http://{LOCAL_IP}:{PORT}/join/2  ║
║  Student 4 (browser) → http://{LOCAL_IP}:{PORT}/join/3  ║
╚══════════════════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Stopped.")
        server.server_close()
        cv2.destroyAllWindows()