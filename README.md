---

# 📚 Online Examination & Education System

A web-based platform designed to conduct online exams, manage students, and streamline the education process efficiently. This system allows students to register, take exams, and view results, while admins can manage users, exams, and performance.

---

## 🚀 Features

* 👨‍🎓 Student Registration & Login
* 🔐 Secure Authentication System
* 📝 Online Exam Interface
* ⏱️ Timer-Based Exams
* 📊 Instant Result Generation
* 📚 Course & Subject Management
* 🧑‍🏫 Admin Dashboard
* 📧 Email Verification (OTP-based)
* 📈 Performance Tracking

---

## 🛠️ Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python (Django)
* **Database:** MySQL
* **Other Tools:** Bootstrap, SMTP (Email Service)

---

## 📂 Project Structure

```
online-examination-education-system/config
│
├── config/          # Main application logic
├── templates/         # HTML templates
├── static/          # CSS, JS, images
├── media/          
├── manage.py
└── requirements.txt
```

---

## ⚙️ Installation & Setup

1. Clone the repository:

```bash
git clone https://github.com/your-username/online-exam-system.git
cd online-exam-system
```

2. Create virtual environment:

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run migrations:

```bash
python manage.py migrate
```

5. Start the server:

```bash
python manage.py runserver
```

6. Open in browser:

```
http://127.0.0.1:8000/
```

---

## 🔑 Environment Variables

Create a `.env` file and add:

```
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
SECRET_KEY=your_secret_key
```

---

## 🧪 Usage

* Register as a student or admin
* Verify email using OTP
* Login to access dashboard
* Attempt exams and view results

---

## 📄 License

This project is licensed under the MIT License.

---

## ⭐ Acknowledgements

* Django Documentation
* Bootstrap Framework

---

