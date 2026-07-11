# 🎓 Online Examination and Education System (OEES)

An intelligent web-based **Online Examination and Education System** developed using **Django and Python**. The platform provides a centralized environment for online learning, course management, examinations, and student monitoring.

The system is designed to simplify educational management by connecting **students, teachers, and administrators** through a secure and user-friendly platform.

## 🚀 Features

* 👨‍🎓 Student Registration and Login
* 👨‍🏫 Teacher Registration and Login
* 🔐 Role-Based Authentication
* 📊 Student and Teacher Dashboards
* 📚 Course Management
* 🎥 Online Course Video Access
* 📝 Online Examination System
* ⏱️ Timed Examinations
* 📊 Automated Result Management
* 👁️ Exam Monitoring and Proctoring
* 📷 Camera-Based Monitoring
* 🤖 AI-Based Object Detection using YOLO
* 🖼️ Image Processing using OpenCV
* 📧 OTP and Email Verification
* 👤 Profile Management
* 📈 Admin Dashboard and System Management

## 🛠️ Technologies Used

### Backend

* Python
* Django
* MySQL

### Frontend

* HTML5
* CSS3
* JavaScript

### AI and Computer Vision

* OpenCV
* YOLO
* Ultralytics
* NumPy

### Development Tools

* Visual Studio Code
* Git
* GitHub
* MySQL

## 📂 Project Structure

```text
Online-Examination-Education-System/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── core/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── student/
│   ├── teacher/
│   └── admin/
│
├── manage.py
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

Move into the project directory:

```bash
cd Online-Examination-Education-System
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

For Command Prompt:

```cmd
venv\Scripts\activate
```

### 4. Install Required Packages

```bash
python -m pip install django pymysql opencv-python ultralytics pillow numpy
```

### 5. Configure MySQL Database

Create a new MySQL database:

```sql
CREATE DATABASE oees_db;
```

Configure the database in `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'oees_db',
        'USER': 'root',
        'PASSWORD': 'YOUR_MYSQL_PASSWORD',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 6. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create an Admin User

```bash
python manage.py createsuperuser
```

### 8. Start the Django Development Server

```bash
python manage.py runserver
```

Open the local development server in your browser.

## 👥 User Roles

### 👨‍🎓 Student

Students can access enrolled courses, watch educational videos, attend online examinations, view examination results, and manage their profiles.

### 👨‍🏫 Teacher

Teachers can manage educational content, create examinations, manage questions, monitor students, and review examination information.

### 🛡️ Administrator

Administrators can manage students, teachers, courses, examinations, and overall system activities through the administrative dashboard.

## 🤖 AI-Based Exam Monitoring

The system integrates **YOLO and OpenCV** for intelligent examination monitoring.

The monitoring system can analyze camera input during online examinations and assist in detecting suspicious objects or activities. This improves the reliability and security of remote examinations.

## 🎯 Project Objective

The main objective of OEES is to provide a unified platform for **online education and examination management**.

The system combines learning resources, online examinations, automated management, and intelligent monitoring to create an efficient digital education environment.

## 🔮 Future Enhancements

* Advanced AI-Based Cheating Detection
* Face Recognition and Identity Verification
* Real-Time Teacher Monitoring Dashboard
* Detailed Student Performance Analytics
* Cloud Deployment
* Mobile Application Support
* Advanced Notification System

## 👨‍💻 Developed By

**Ankit Saha**
**Abhishek Chakroborty**
**Anirudha Gorai**
**Prithwish Narayan Majumder**

B.Tech Computer Science and Engineering

## 📄 License

This project is developed for educational and academic purposes.
