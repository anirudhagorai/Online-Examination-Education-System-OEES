# 🎓 Online Examination and Education System (OEES) — "EduExam"

<p align="center">
  <img src="https://img.shields.io/badge/Django-Backend-black?style=for-the-badge&logo=django">
  <img src="https://img.shields.io/badge/MySQL-Database-blue?style=for-the-badge&logo=mysql">
  <img src="https://img.shields.io/badge/Python-3.10%2B-yellow?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/OpenCV%20%2B%20YOLOv8-AI%20Proctoring-red?style=for-the-badge">
  <img src="https://img.shields.io/badge/Final%20Year%20Project-2025--26-success?style=for-the-badge">
</p>

---

## 📖 Overview

Paper-based exams and manual course management remain a persistent challenge for educational institutions of all sizes — faculty lose hours organizing question papers, students wait days for results, and teacher–student communication gets lost across scattered channels.

**EduExam (OEES)** is a self-hosted web platform that brings course management, timed examinations, student communication, and **AI-powered exam proctoring** into a single application any college can run on its own server — without expensive licensing, cloud lock-in, or a dedicated IT team.

The backend is built with **Django + MySQL**, the frontend is deliberately framework-free (**HTML5, CSS3, vanilla JS**) to keep it lightweight and maintainable, and a separate **ProctorScope** module uses OpenCV and YOLOv8 to monitor students in real time during live exams.

---

## 🎯 Objectives

- Design a role-based web app supporting distinct **Student** and **Teacher** dashboards.
- Provide secure registration via **OTP-based email verification**.
- Build a full **course management module** with YouTube-integrated video content.
- Implement an **online examination module** with scheduling, duration timers, and automated status tracking (upcoming / ongoing / completed / missed).
- Deliver an **announcement & assignment** broadcasting system with priority levels, due dates, and attachments.
- Enable **threaded direct messaging** between students and teachers.
- Enforce security through CSRF protection, `@login_required` gating, role-based access control, and hashed password storage.
- Add an **AI-assisted proctoring layer** to detect violations during live exams.

---

## 👨‍💻 Project Team

### Department of Computer Science & Engineering
### Siliguri Institute of Technology

| Name | Roll No |
|------|---------|
| Abhishek Chakroborty | 11900122083 |
| Anirudha Gorai | 11900122123 |
| Ankit Saha | 11900122085 |
| Prithwish Narayan Majumder | 11900122118 |

### Project Guide

**Prof. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_** *(add guide's name)*

---

## 🏗️ System Architecture

EduExam follows Django's **Model–View–Template (MVT)** pattern, a close relative of MVC. Schema changes rarely touch templates, and frontend changes never require a migration.

```text
                Browser (Student / Teacher)
                          │
                          ▼
                  Django URL Router
                (50+ routes, 4 groups)
                          │
                          ▼
        ┌─────────────────────────────────┐
        │        Views (core/views.py)    │
        │  auth · courses · exams ·       │
        │  announcements · messaging      │
        └─────────────────────────────────┘
                          │
                          ▼
              Django ORM  ──────────────►  MySQL Database
                          │
                          ▼
              HTML Templates (Django Template Tags)
                          │
                          ▼
                  Rendered Page / JSON (AJAX)


        ┌──────────────────────────────────────┐
        │     ProctorScope (independent)       │
        │  Python http.server + ThreadingMixIn │
        │  OpenCV (face/eye) + YOLOv8 (phone)  │
        │  Live MJPEG stream + violation log   │
        └──────────────────────────────────────┘
```

---

## 🗃️ Database Design

Six core models drive the data layer, connected through Django's ORM:

| Model | Key Fields | Relationships |
|-------|-----------|----------------|
| **Profile** | role, dob, roll_number, teacher_id, otp, otp_created_at, is_verified, otp_attempts | OneToOne with Django's built-in User |
| **Course** | name, description, status, color, progress, grade, youtube_id, total_videos | ForeignKey to teacher; ManyToMany to enrolled students |
| **CourseProgress** | progress (0–100) | FK to student and course; unique-together pair |
| **Exam** | title, duration, total_marks, total_questions, status, scheduled_date | FK to course; ManyToMany to assigned students |
| **Announcement** | title, message, type, priority, due_date, attachment, is_active | FK to teacher and course; ManyToMany `read_by` students |
| **Message** | subject, body, attachment, is_read, created_at | FK to sender/receiver; self-referential FK for threading |

`Profile` extends Django's built-in `User` via `OneToOneField` rather than replacing it — preserving Django's auth machinery (sessions, hashing, login decorators) while adding institution-specific fields.

---

## 📦 Core Modules

### 🔐 Authentication Module
- Students register with name, email, and roll number; teachers use a unique teacher ID.
- A 6-digit OTP is emailed on registration, expiring after a short window, with limited retry attempts and a resend option.
- Forgot-password flow reuses the same OTP pattern.
- Passwords are hashed with Django's **PBKDF2-SHA256**; raw passwords are never stored.

### 🎓 Student Module
- Dashboard summary: enrolled courses, upcoming tests, unread announcements, recent activity.
- Join/drop courses in one click; track per-course and overall progress.
- Exams split into upcoming / ongoing / completed / missed; results appear once an exam closes.
- Announcement inbox with unread badge counts; threaded messaging with teachers.

### 🧑‍🏫 Teacher Module
- Dashboard: total students, active courses, recent announcements/messages.
- Create/edit/remove courses with optional embedded YouTube playlists.
- Create exams with title, course, marks, duration, schedule, and target students.
- Post announcements/assignments with priority levels, due dates, and attachments.
- Reply to student messages in a single threaded conversation.

### 🕵️ ProctorScope — AI Proctoring Module
An independent Python module (its own HTTP server, port 5000) that monitors students live during exams:

- **Face & eye detection** — OpenCV Haar Cascade classifiers.
- **Head-movement tracking** — `MovementTracker` analyzes the last 8 face centroids.
- **Phone detection** — YOLOv8 nano (COCO class 67).
- **Earphone detection** — geometric heuristic around the ear region.
- **Noise filtering** — a `Stabilizer` class uses a 10-frame sliding window before logging a violation.
- **Violation types tracked:** `FACE_ABSENT`, `MULTIPLE_FACES`, `PHONE_DETECTED`, `EARPHONE_DETECTED`, `TAB_SWITCH`, `FULLSCREEN_EXIT`.
- **Live proctor dashboard** streaming MJPEG feeds from all connected students with a real-time violation log.

---

## 🛠️ Technology Stack

### Backend
- Python, Django 4.x / 5.x (MVT pattern, ORM, built-in auth & admin)
- MySQL 8.0+ (via `mysqlclient`)
- Django Email backend + Gmail SMTP (OTP delivery)
- WhiteNoise (static file serving)
- `python-decouple` / `.env` for secrets management

### Frontend
- HTML5, CSS3, JavaScript (ES6+) — no heavy frontend framework by design
- Fetch API for AJAX interactions (OTP checks, enrollment toggles, read-status updates)

### AI Proctoring (ProctorScope)
- OpenCV 4.x (`opencv-python`) — Haar Cascade face/eye detection
- YOLOv8 nano (Ultralytics) — object detection for phones
- Python `http.server` + `ThreadingMixIn` — concurrent per-student streaming
- Python `threading` — one camera thread per student, guarded by per-student locks

### Deployment
- Gunicorn + Nginx (production) / Django dev server (testing)
- Git + GitHub for version control

---

## 🚀 Installation

> ⚠️ **Note:** These are standard Django setup steps inferred from the project's tech stack. Update the repo URL, exact `requirements.txt`, and any project-specific `.env` variables once available.

```bash
# Clone the repository
git clone https://github.com/yourusername/oees-eduexam.git
cd oees-eduexam

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (.env)
# DB credentials, SECRET_KEY, Gmail SMTP app password, etc.

# Apply database migrations
python manage.py migrate

# Run the development server
python manage.py runserver
```

Then open `http://127.0.0.1:8000/`.

To run the ProctorScope module separately:

```bash
cd proctorscope
python server.py
```

---

## ✅ Project Features

✅ Role-Based Dashboards (Student / Teacher)

✅ OTP-Based Secure Registration

✅ Course Management with YouTube Integration

✅ Scheduled Online Examinations

✅ Priority-Based Announcements & Assignments

✅ Threaded Direct Messaging

✅ AI-Powered Webcam Proctoring (ProctorScope)

✅ CSRF Protection & Hashed Passwords

✅ Django Migrations for Schema Versioning

---

## ⚠️ Known Limitations

- In-browser question answering with automated scoring is not yet built — exam scheduling/status tracking is complete, but the results page currently depends on this pending module.
- Designed for single-institution deployment; multi-tenancy would need architectural changes.
- Notifications are pull-based (on page load), not real-time push.

---

## 🔬 Future Scope

- **In-Browser Answer Submission** — question bank + automated MCQ scoring
- **Live Push Notifications** — Django Channels + WebSockets
- **Performance Analytics Dashboard** — visual trends for teachers
- **REST API & Mobile Apps** — Django REST Framework layer for Android/iOS
- **Multi-Institution Support** — scoped data namespaces for multi-tenant deployment
- **AI Essay Grading** — NLP-based feedback and plagiarism flagging
- **Integrated Video Classes** — embedded Jitsi Meet conferencing
- **Gamification** — completion certificates, badges, progress indicators

---

## 📚 References

[1] Bhadouria A., Gupta P., Bindal P., Madan K., Sonal S. *Automated Examination System Using Machine Learning and Natural Language Processing*, IC3 2024.

[2] Django Software Foundation. *Django Documentation* (v5.0).

[3] Ferraiolo D. F., Barkley J. F., Kuhn D. R. *A Role-Based Access Control Model and Reference Implementation Within a Corporate Intranet*, ACM TISSEC, 1999.

[4] Islam K., Ahmadi P., Yousaf S. *A Survey of Learning Management Systems and Synchronous Distance Education Tools*, arXiv:1711.10585, 2017.

[5] Jocher G., Chaurasia A., Qiu J. *Ultralytics YOLOv8* (v8.0.0) [Computer software], 2023.

[6] OpenCV Team. *OpenCV Documentation* (v4.x), 2024.

[7] Oracle Corporation. *MySQL 8.0 Reference Manual*, 2024.

[8] Sasikumar S., Bijlani K. *New Features for Webcam Proctoring Using Python and OpenCV*, IJRTE, 2021.

[9] Kaliski B. *PKCS #5: Password-Based Cryptography Specification, Version 2.0* (RFC 2898), IETF, 2000.

[10] Viola P., Jones M. *Rapid Object Detection Using a Boosted Cascade of Simple Features*, CVPR 2001.

[11] W3C / OWASP Foundation. *Cross-Site Request Forgery (CSRF) Prevention Cheat Sheet*, 2024.

---

© This project was developed for academic and research purposes as part of the Bachelor of Technology (B.Tech) degree requirement at Siliguri Institute of Technology.
