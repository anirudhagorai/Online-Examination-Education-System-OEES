from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator


class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # Added to easily track "newly joined" users for the dashboard
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    dob = models.DateField(null=True, blank=True)
    # student fields
    roll_number = models.CharField(
        max_length=20, blank=True, null=True, unique=True)

    # teacher fields
    teacher_id = models.CharField(
        max_length=20, blank=True, null=True, unique=True)

    # otp fields
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    otp_attempts = models.IntegerField(default=0)

    admin_approved = models.BooleanField(default=False)
    admin_approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    is_suspended = models.BooleanField(default=False)
    suspended_at     = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True, null=True)

    # otp Expiry Function
    def is_otp_expired(self):
        if self.otp_created_at:
            expiry_time = self.otp_created_at + timedelta(minutes=5)
            return timezone.now() > expiry_time
        return True

    def __str__(self):
        return self.user.username


class Course(models.Model):
    # Added choices to support admin approval workflows
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, related_name='taught_courses', null=True, blank=True)

    # Updated to use the new choices
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft'
    )
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_courses'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    color = models.CharField(max_length=20, default='blue')
    progress = models.IntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    total_videos = models.IntegerField(default=0)
    total_duration = models.CharField(max_length=20, blank=True)
    # Local video fields
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    thumbnail = models.ImageField(
        upload_to='thumbnails/', blank=True, null=True)

    students = models.ManyToManyField(
        User, blank=True, related_name='enrolled_courses')

    class Meta:
      ordering = ['-created_at']


    def __str__(self):
      return self.name



class CourseProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)

    class Meta:
        unique_together = ('student', 'course')


class Announcement(models.Model):
    TYPE_CHOICES = (
        ('announcement', 'Announcement'),
        ('assignment', 'Assignment'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='announcement')
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='medium')
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='announcements')
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)  # for assignment
    attachment = models.FileField(
        upload_to='announcement/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Track which students have read it
    read_by = models.ManyToManyField(
        User, blank=True, related_name='read_announcements')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    subject = models.CharField(max_length=250)
    body = models.TextField()
    attachment = models.FileField(
        upload_to='message_attachments/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender.username} -> {self.receiver.username}: {self.subject}'


class ExamCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Exam Categories"

    def __str__(self):
        return self.name


class Exam(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    ]

    title = models.CharField(max_length=200)
    # course = models.ForeignKey(
    #     Course, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(
        ExamCategory, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_exams', null=True)

    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=60)

    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)

    # status = models.CharField(max_length=20, default='draft')

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft')
    # scheduled_date = models.DateTimeField(null=True, blank=True)
    students = models.ManyToManyField(
        User, blank=True, related_name="enrolled_exams")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Video(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video_file = models.FileField(
        upload_to='videos/'
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/'
    )

    def __str__(self):
        return f"{self.course.name} Video"


class Resource(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    pdf_file = models.FileField(
        upload_to='resources/'
    )
    title = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.pdf_file.name


class StudentExamAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='exam_attempts')
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

    class Meta:
        ordering = ['-started_at']


class MonthlyAnalyticsSummary(models.Model):
    """Simplified to track exactly what the admin needs (exams conducted by month/year)"""
    year = models.IntegerField()
    month = models.IntegerField()
    total_exams_conducted = models.IntegerField(default=0)

    class Meta:
      unique_together = ('year', 'month')
      ordering = ['year', 'month']

    def __str__(self):
      return f"{self.year}-{self.month:02d}"


class TeacherApprovalLog(models.Model):
    """
    Tracks every admin approval / rejection action on a teacher account.
    Shown in the admin_teachers panel audit trail.
    """
    ACTION_CHOICES = [
        ('approved',  'Approved'),
        ('rejected',  'Rejected'),
        ('revoked',   'Revoked'),
        ('re_approved', 'Re-Approved'),
    ]

    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='approval_logs'
    )
    admin = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='approval_actions'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Teacher Approval Log'

    def __str__(self):
        return f"{self.admin} {self.action} {self.teacher} at {self.created_at:%d %b %Y}"


class StudentActivityLog(models.Model):
    """
    Admin audit trail for every action taken on a student account.
    Stored separately from ActivityLog so it can be shown per-student.
    """
    ACTION_CHOICES = [
        ('suspended',  'Suspended'),
        ('unsuspended', 'Unsuspended'),
        ('deleted',    'Deleted'),
        ('edited',     'Edited'),
        ('enrolled',   'Enrolled in Course'),
        ('unenrolled', 'Unenrolled from Course'),
        ('locked',     'Account Locked'),
        ('unlocked',   'Account Unlocked'),
        ('password_reset', 'Password Reset'),
    ]

    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='student_activity_logs'
    )
    admin = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='student_admin_actions'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    detail = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Activity Log'

    def __str__(self):
        return f"{self.action} on {self.student} by {self.admin}"



class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('course', 'Course'),
        ('exam', 'Exam'),
        ('announcement', 'Announcement'),
        ('message', 'Message'),
        ('user', 'User'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )

    action_type = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        default='other'
    )

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.user.username} - {self.action_type}"


class AdminAnnouncement(models.Model):
    CATEGORY_CHOICES = [
        ('course', 'Course Update'),
        ('exam', 'Exam & Assessment'),
        ('result', 'Result & Certificate'),
        ('approval', 'Approval & Review'),
        ('enrollment', 'Enrollment'),
        ('system', 'System & Maintenance'),
        ('event', 'Event'),
    ]

    TARGET_CHOICES = [
        ('student', 'Students Only'),
        ('teacher', 'Teachers Only'),
        ('all', 'All Users'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default='system')
    target_role = models.CharField(
        max_length=10, choices=TARGET_CHOICES, default='all')
    priority = models.CharField(max_length=10, default='medium')

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    related_course = models.ForeignKey(
        'Course', on_delete=models.SET_NULL, null=True, blank=True)
    related_exam = models.ForeignKey(
        'Exam', on_delete=models.SET_NULL, null=True, blank=True)


    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.question_text[:50]


class ExamOption(models.Model):
    question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text
class StudentExamAttempt(models.Model):
    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("submitted", "Submitted"),
        ("failed", "Failed"),
        ("passed", "Passed"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    score = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)

    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    unanswered = models.IntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

