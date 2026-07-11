import datetime
from urllib import request  # Add this at the top if not already present
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.db import transaction, models as db_models
from django.urls import reverse
from django.utils import timezone
from django.core.mail import EmailMessage, send_mail, send_mass_mail
from django.db.models import Q
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.template.loader import render_to_string
import random
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .decorators import admin_required
from .models import Profile, Course, CourseProgress, Exam, Video, Resource, Announcement, Message, StudentExamAttempt, ExamCategory, MonthlyAnalyticsSummary, ActivityLog, AdminAnnouncement
import json
from datetime import timedelta, datetime
from django.db.models import Count, Avg
from django.contrib.auth.hashers import make_password
from django.utils.timesince import timesince
from .models import Profile, Course, CourseProgress, Exam, ExamQuestion, ExamOption, Video, Resource, Announcement, Message, StudentExamAttempt, ExamCategory, MonthlyAnalyticsSummary, ActivityLog, AdminAnnouncement
from django.utils import timezone
from django.contrib.auth.decorators import login_required
# ------------------- Home -------------------
def home(request):
  return render(request,'core/home.html',{})

def login_register(request,role):
  return render(request,'core/login_register.html',{"role":role})

@require_http_methods(["GET","POST"])
def logout_user(request):
  logout(request)
  return redirect('home')

def auth_page(request, role):
  return render(request, 'core/login_register.html', {'role': role})


def get_user_context(user):
  first = user.first_name[0].upper() if user.first_name else ''
  last = user.last_name[0].upper() if user.last_name else ''
  initials = (first + last) or user.username[0].upper()
  return{
    'initials' : initials,
    'role' : user.profile.role,
    'fullname' : user.get_full_name() or user.username,
    'profile': user.profile,
    'email': user.email,
  }


# ──────────────────────────────────────────────────────────────────────
#  HELPER: General Activity Log
# ──────────────────────────────────────────────────────────────────────
def _log_activity(admin_user, description, icon='info', color='blue'):
    """Safe general activity logging"""
    try:
        from .models import ActivityLog
        ActivityLog.objects.create(
            user=admin_user,
            action_type='admin_action',
            description=description,
            # You can extend the model later with icon/color if needed
        )
    except Exception as e:
        print(f"Activity log error: {e}")


# Global Student Login Control (Add near top, after imports)
if not hasattr(settings, 'STUDENT_LOGIN_ENABLED'):
    settings.STUDENT_LOGIN_ENABLED = True

# ------------------- Student -------------------
@login_required(login_url='/login_register/student')
def student_dashboard(request):
  my_courses = Course.objects.filter(
      students=request.user).prefetch_related('videos')
  for course in my_courses:
    prog = CourseProgress.objects.filter(
        student=request.user, course=course).first()
    course.progress = prog.progress if prog else 0

  total = my_courses.count()
  completed = sum(1 for c in my_courses if c.progress >= 100)
  avg = round(sum(c.progress for c in my_courses) / total) if total > 0 else 0

  exams = Exam.objects.filter(students=request.user)

  context = {
      'active_page': 'dashboard',
      'current_courses': my_courses,
      'total_courses': total,
      'completed_courses': completed,
      'avg_progress': avg,
      'upcoming_exams': exams.filter(status='upcoming'),
      'ongoing_exams': exams.filter(status='ongoing'),
      **get_user_context(request.user),
  }
  return render(request, 'core/student/student_dashboard.html', context)

@login_required(login_url='/login_register/student')
def student_courses(request):
  # Courses student is enrolled in
  inprogress_count=0
  my_courses = Course.objects.filter(
      students=request.user).prefetch_related('videos')

  # Add progress to each course
  for course in my_courses:
    prog = CourseProgress.objects.filter(
        student=request.user, course=course).first()
    course.progress = prog.progress if prog else 0
    # Set status based on student's own progress
    if course.progress >= 100:
      course.student_status = 'completed'
    elif course.progress > 0:
      course.student_status = 'active'
    else:
      course.student_status = 'active'

  # All courses not enrolled in - for enrollment modal
  available_courses = Course.objects.exclude(
      students=request.user).prefetch_related('videos')

  completed_count = sum(1 for c in my_courses if c.progress >= 100)
  inprogress_count = sum(1 for c in my_courses if 0 < c.progress < 100)

  total_prog = sum(c.progress for c in my_courses)
  avg_progress = round(total_prog / my_courses.count()
                       ) if my_courses.count() > 0 else 0
  context = {
      'active_page': 'courses',
      'courses': my_courses,
      'available_courses': available_courses,
      'completed_count': completed_count,
      'inprogress_count': inprogress_count,
      'avg_progress': avg_progress,
      **get_user_context(request.user),
  }
  return render(request, 'core/student/student_courses.html', context)


@login_required(login_url='/login_register/student')
def enroll_course(request,course_id):
  if request.method == 'POST':
    try:
      course = Course.objects.get(id=course_id)
      if course.students.filter(id=request.user.id).exists():
        return JsonResponse({
            'status': 'already',
            'message': 'You are already enrolled in this course!'
        })

      course.students.add(request.user)

      CourseProgress.objects.get_or_create(
          student=request.user,
          course=course,
          defaults={'progress': 0}
      )
      return JsonResponse({
          'status': 'ok',
          'message': f'Successfully enrolled in {course.name}!'
      })
    except Course.DoesNotExist:
      return JsonResponse({
          'status': 'error',
          'message': 'Invalid request.'
      })
  return JsonResponse({
      'status': 'error',
      'message': 'Invalid request.'
  })


@login_required(login_url='/login_register/student')
def unenroll_course(request,course_id):
  if request.method == 'POST':
    try:
      course = Course.objects.get(id=course_id)
      course.students.remove(request.user)
      CourseProgress.objects.filter(
          student=request.user, course=course
      ).delete()
      return JsonResponse({
          'status': 'ok',
          'message': 'Unenrolled successfully'
      })
    except Course.DoesNotExist:
      return JsonResponse({
          'status': 'error',
          'message': 'Course not found.'
      })
  return JsonResponse({
      'status': 'error',
      'message': 'Invalid request.'
  })

from datetime import datetime
from django.utils import timezone

from datetime import datetime
from django.utils import timezone

@login_required(login_url='/login_register/student')
def student_examinations(request):

    exams = Exam.objects.all()

    now = timezone.localtime()

    upcoming_exams = []
    ongoing_exams = []
    completed_exams = []
    missed_exams = []

    print("Current Time:", now)

    for exam in exams:

        if not exam.scheduled_date or not exam.scheduled_time:
            continue

        exam_datetime = timezone.make_aware(
            datetime.combine(
                exam.scheduled_date,
                exam.scheduled_time
            )
        )

        exam_end = exam_datetime + timezone.timedelta(
            minutes=exam.duration_minutes
        )

        print("--------------------------------")
        print("Exam:", exam.title)
        print("Start:", exam_datetime)
        print("End:", exam_end)

        if now < exam_datetime:
            print("Status = Upcoming")
            upcoming_exams.append(exam)

        elif exam_datetime <= now <= exam_end:
            print("Status = Ongoing")
            ongoing_exams.append(exam)

        else:
            print("Status = Completed")
            completed_exams.append(exam)

    print("Upcoming:", len(upcoming_exams))
    print("Ongoing:", len(ongoing_exams))
    print("Completed:", len(completed_exams))

    return render(
        request,
        "core/student/student_examinations.html",
        {
            "upcoming_exams": upcoming_exams,
            "ongoing_exams": ongoing_exams,
            "completed_exams": completed_exams,
            "missed_exams": missed_exams,

            "upcoming_count": len(upcoming_exams),
            "ongoing_count": len(ongoing_exams),
            "completed_count": len(completed_exams),
            "missed_count": len(missed_exams),
        }
    )


@login_required(login_url='/login_register/student')
def student_results(request):
  context = {
    'active_page': 'results',
    **get_user_context(request.user),

  }
  return render(request, 'core/student/student_results.html', context)


@login_required(login_url='/login_register/student')
def student_profile(request):
  profile = request.user.profile
  context = {
      'active_page': 'profile',
      'profile': profile,
      'email': request.user.email,
      **get_user_context(request.user),
  }
  return render(request, 'core/student/student_profile.html', context)


@login_required(login_url='/login_register/student')
def student_announcements(request):
  # Announcements from Teachers
  announcements = Announcement.objects.filter(
      is_active=True).order_by('-created_at')

  # Student sent messages
  sent_messages = Message.objects.filter(
      sender=request.user, parent__isnull=True).prefetch_related('replies').order_by('-created_at')

  # Teacher inbox messages to student
  inbox_messages = Message.objects.filter(
      receiver=request.user, parent__isnull=True).prefetch_related('replies').order_by('-created_at')

  # FIXED: Get ONLY teachers from courses the student is enrolled in
  my_courses = Course.objects.filter(students=request.user)
  teachers = User.objects.filter(
      id__in=my_courses.values('teacher_id')
  ).distinct().exclude(id=request.user.id)

  context = {
      'active_page': 'announcements',
      'announcements': announcements,
      'sent_messages': sent_messages,
      'inbox_messages': inbox_messages,
      'teachers': teachers,          # Now only teachers
      'total': announcements.count(),
      **get_user_context(request.user),
  }
  return render(request, 'core/student/student_announcements.html', context)


@login_required(login_url='/login_register/student')
def student_send_announcement(request):
  if request.method == 'POST':
    try:
      parent_id = request.POST.get('parent_id')
      body = request.POST.get('body', '').strip()

      if not body:
        return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'})

      if parent_id:
        original = Message.objects.get(id=parent_id)
        subject = f"Re: {original.subject.replace('Re:', '')}"
        msg = Message.objects.create(sender=request.user, receiver=original.sender, subject=subject, body=body, parent=original)
        original.is_read = True
        original.save()
      else:
        receiver_id = request.POST.get('receiver_id')
        subject = request.POST.get('subject', '').strip()
        if not receiver_id or not subject:
          return JsonResponse({'status': 'error', 'message': 'Teacher and subject required.'})
        receiver = User.objects.get(id=receiver_id)
        msg = Message.objects.create(sender=request.user, receiver=receiver, subject=subject, body=body)

      # Handle attachment
      if 'attachment' in request.FILES:
        file = request.FILES['attachment']
        # Max 10MB
        if file.size > 10 * 1024 * 1024:
          msg.delete()
          return JsonResponse({'status': 'error', 'message': 'File too large. Max 10MB allowed.'})
        msg.attachment = file
        msg.save()

      send_direct_message_email(msg)
      return JsonResponse({'status': 'ok', 'message': 'Message sent to teacher successfully!'})
    except Exception as e:
      return JsonResponse({'status': 'error', 'message': str(e)})
  return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


# View Announcement

@login_required(login_url='/login_register/student')
def student_view_announcement(request, ann_id):
  if request.method == 'POST':
    try:
      inbox_messages
      msg = Message.objects.get(id=ann_id, receiver=request.user)
      msg.is_read = True
      msg.save()
      return JsonResponse({
        'status': 'ok',
        'subject': msg.subject,
        'body': msg.body,
        'sender': msg.sender.get_full_name() or msg.sender.username,
        'created_at': msg.created_at.strftime('%d %B %Y, %I:%M %p'),
        'attachment_name': msg.get_attachment_name(),
        'attachment_url': msg.attachment.url if msg.attachment else None
      })
    except Message.DoesNotExist:
      return JsonResponse({'status': 'error', 'message':'Message not found.'})
  return JsonResponse({'status': 'error'})


# Delete Announcement
@login_required(login_url='/login_register/student')
def student_delete_announcement(request, ann_id):
  if request.method == 'POST':
    try:
      ann = Message.objects.get(id=ann_id, sender=request.user)
      ann.delete()
      return JsonResponse({'status': 'ok', 'message': 'Deleted Successfully'})
    except Announcement.DoesNotExist:
      return JsonResponse({'status': 'error', 'message': 'Not found'})
  return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@login_required
def student_recent_announcements(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error'})

    announcements = Announcement.objects.filter(
        is_active=True).order_by('-created_at')[:10]

    data = []
    for ann in announcements:
        data.append({
            'id': ann.id,
            'title': ann.title,
            'message': ann.message,
            'teacher': ann.teacher.get_full_name() or ann.teacher.username,
            'time_ago': timesince(ann.created_at) + ' ago',
            'is_new': True  # You can improve this logic later
        })

    return JsonResponse({
        'status': 'ok',
        'announcements': data,
        'unread_count': 3  # Update with real count later
    })

# ------------------- Update Profile (shared) -------------------
@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        profile = user.profile

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                return JsonResponse({'status': 'error', 'message': 'This email is already in use.'})
            return JsonResponse({'status': 'email_otp_required', 'new_email': email})

        if full_name:
            user.first_name = full_name

        user.save()

        if profile.role == 'student':
            dob = request.POST.get('dob', '').strip()
            if dob:
                profile.dob = dob

        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
        return JsonResponse({'status': 'ok', 'message': 'Profile updated successfully!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@login_required
def send_email_change_otp(request):
    if request.method == 'POST':
        new_email = request.POST.get('new_email', '').strip()
        if not new_email:
            return JsonResponse({'status': 'error', 'message': 'No email provided.'})

        if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
            return JsonResponse({'status': 'error', 'message': 'This email is already in use.'})

        otp = str(random.randint(100000, 999999))
        profile = request.user.profile
        profile.otp = otp
        profile.otp_created_at = timezone.now()
        profile.otp_attempts = 0
        profile.save()

        request.session['pending_email'] = new_email

        send_mail(
            "Email Change Verification OTP",
            f"Your OTP to confirm your new email is {otp}. It is valid for 2 minutes.",
            settings.EMAIL_HOST_USER,
            [new_email],
            fail_silently=False,
        )

        return JsonResponse({'status': 'success', 'message': f'OTP sent to {new_email}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@login_required
def verify_email_change_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        user = request.user
        profile = user.profile

        new_email = request.session.get('pending_email')
        if not new_email:
            return JsonResponse({'status': 'error', 'message': 'Session expired. Please try again.'})

        if profile.is_otp_expired():
            return JsonResponse({'status': 'expired', 'message': 'OTP expired. Please request a new one.'})

        if profile.otp_attempts >= 3:
            return JsonResponse({'status': 'blocked', 'message': 'Too many wrong attempts. Please try again later.'})

        if entered_otp == profile.otp:
            user.email = new_email
            user.save()
            profile.otp = None
            profile.otp_created_at = None
            profile.otp_attempts = 0
            profile.save()
            del request.session['pending_email']
            return JsonResponse({'status': 'success', 'message': 'Email updated successfully!', 'new_email': new_email})
        else:
            profile.otp_attempts += 1
            profile.save()
            remaining = 3 - profile.otp_attempts
            return JsonResponse({'status': 'error', 'message': f'Invalid OTP. {remaining} attempt(s) remaining.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


# ------------------- Teacher -------------------


@login_required(login_url='/login_register/teacher')
def teacher_dashboard(request):
    teacher = request.user

    # Teacher's exams
    exams = Exam.objects.filter(created_by=teacher)

    # Dashboard statistics
    total_courses = 0          # No Course relation in Exam
    total_students = 0         # Update later if needed
    total_exams = exams.count()
    active_courses = 0
    completed_exams = exams.filter(status='completed').count()

    # Recent data
    recent_courses = []
    recent_exams = exams.order_by('-id')[:5]

    recent_students = []
    top_students = []

    pending_submissions = 0
    upcoming_exams_count = exams.filter(status='upcoming').count()

    announcements_count = 0
    recent_activities = []

    def get_time_of_day():
        current_hour = timezone.localtime(timezone.now()).hour
        if current_hour < 12:
            return "Morning"
        elif current_hour < 17:
            return "Afternoon"
        return "Evening"

    context = {
        'active_page': 'dashboard',
        'teacher': teacher,
        'time_of_day': get_time_of_day(),

        'total_courses': total_courses,
        'total_students': total_students,
        'total_exams': total_exams,
        'active_courses': active_courses,
        'completed_exams': completed_exams,

        'recent_courses': recent_courses,
        'recent_exams': recent_exams,
        'recent_students': recent_students,
        'top_students': top_students,

        'pending_submissions': pending_submissions,
        'upcoming_exams_count': upcoming_exams_count,
        'announcements_count': announcements_count,
        'recent_activities': recent_activities,

        **get_user_context(request.user),
    }

    return render(request, 'core/teacher/teacher_dashboard.html', context)

@login_required(login_url='/login_register/teacher')
def teacher_courses(request):
#   courses = Course.objects.filter(teacher=request.user)
  for course in courses:
    students = course.students.all()
    if students.exists():
      from .models import CourseProgress
      total = sum(
          CourseProgress.objects.filter(
              course=course, student=s
          ).first().progress or 0
          for s in students
      )
      course.avg_progress = round(total/students.count())
    else:
      course.avg_progress = 0

  context = {
      'active_page': 'courses',
      **get_user_context(request.user),
      'courses': courses,
      'total_courses': courses.count(),
      'active_courses': courses.filter(status='active').count(),
      'total_students': User.objects.filter(enrolled_courses__in=courses).distinct().count(),
      'total_videos': sum(c.total_videos or 0 for c in courses),
  }
  return render(request, 'core/teacher/teacher_courses.html', context)


@login_required(login_url='/login_register/teacher')
def teacher_course_player(request, course_id):
    try:
        course = Course.objects.get(id=course_id, teacher=request.user)
        video = course.videos.first()
        context = {
            'active_page': 'courses',
            'course': course,
            'video': video,
            **get_user_context(request.user),
        }
        return render(request, 'core/teacher/teacher_courseplayer.html', context)
    except Course.DoesNotExist:
        messages.error(request, "Course not found.")
        return redirect('teacher_courses')


@login_required(login_url='/login_register/teacher')
def teacher_replace_video(request, course_id):
    if request.method == 'POST':
        try:
            course = Course.objects.get(id=course_id, teacher=request.user)
            video_file = request.FILES.get('video_file')
            thumbnail = request.FILES.get('thumbnail')
            pdf_file = request.FILES.get('pdf_file')
            video = course.videos.first()
            if video:
                if video_file:
                    video.video_file = video_file
                if thumbnail:
                    video.thumbnail = thumbnail
                if pdf_file:
                    video.pdf_file = pdf_file
                video.save()
            else:
                if video_file and thumbnail:
                    Video.objects.create(
                        course=course, video_file=video_file, thumbnail=thumbnail, pdf_file=pdf_file)
            return JsonResponse({'status': 'ok', 'message': 'Video updated successfully!'})
        except Course.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Course not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@login_required(login_url='/login_register/teacher')
def teacher_add_course(request):
    if request.method == 'POST':
        try:
            course = Course.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                teacher=request.user,
                status='pending',                    # ← Auto set to pending
                total_videos=request.POST.get('total_videos') or 0,
                total_duration=request.POST.get('total_duration', ''),
            )

            # Handle video + thumbnail
            video_file = request.FILES.get('video_file')
            thumbnail = request.FILES.get('thumbnail')

            if video_file and thumbnail:
                Video.objects.create(
                    course=course,
                    video_file=video_file,
                    thumbnail=thumbnail
                )

            # Handle PDF resources
            pdf_files = request.FILES.getlist('pdf_files')
            for pdf in pdf_files:
                Resource.objects.create(
                    course=course, pdf_file=pdf, title=pdf.name)

            _log_activity(
                request.user,
                f'Created new course "{course.name}" (Pending Admin Approval)'
            )

            return JsonResponse({
                'status': 'ok',
                'message': f'Course "{course.name}" created successfully! Waiting for admin approval.'
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@login_required(login_url='/login_register/teacher')
def teacher_edit_course(request, course_id):
    if request.method == 'POST':
        try:
            course = Course.objects.get(id=course_id, teacher=request.user)

            course.name = request.POST.get('name')
            course.description = request.POST.get('description', '')
            course.total_videos = request.POST.get('total_videos') or 0
            course.total_duration = request.POST.get('total_duration', '')

            # ← IMPORTANT: Prevent teacher from activating course directly
            requested_status = request.POST.get('status', course.status)
            if requested_status == 'active' and course.status != 'approved':
                course.status = 'pending'   # Force back to pending
            else:
                course.status = requested_status

            course.save()

            # Handle files
            video_file = request.FILES.get('video_file')
            thumbnail = request.FILES.get('thumbnail')

            if video_file or thumbnail:
                video = course.videos.first()
                if video:
                    if video_file:
                        video.video_file = video_file
                    if thumbnail:
                        video.thumbnail = thumbnail
                    video.save()
                else:
                    Video.objects.create(
                        course=course,
                        video_file=video_file,
                        thumbnail=thumbnail
                    )

            pdf_files = request.FILES.getlist('pdf_files')
            for pdf in pdf_files:
                Resource.objects.create(
                    course=course, pdf_file=pdf, title=pdf.name)

            return JsonResponse({
                'status': 'ok',
                'message': f'Course "{course.name}" updated! Status is now: {course.status}'
            })

        except Course.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Course not found.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

@login_required(login_url='/login_register/teacher')
def teacher_delete_course(request, course_id):
  if request.method == 'POST':
    try:
      course = Course.objects.get(id=course_id, teacher=request.user)
      name = course.name
      course.delete()
      return JsonResponse({'status': 'ok', 'message': f'"{name}" deleted!'})
    except Course.DoesNotExist:
      return JsonResponse({'status': 'error', 'message': 'Course not found.'})
  return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


# @login_required(login_url='/login_register/teacher')
# def teacher_examinations(request):
#   context = {
#       'active_page': 'examinations',
#       **get_user_context(request.user),
#   }
#   return render(request, 'core/teacher/teacher_examinations.html', context)

@login_required(login_url='/login_register/teacher')
def teacher_examinations(request):

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        duration = request.POST.get('duration')
        marks = request.POST.get('marks')
        pass_marks = request.POST.get('pass_marks')
        exam_date = request.POST.get('exam_date')
        exam_time = request.POST.get('exam_time')

        question_ids = request.POST.getlist('question_id[]')
        questions = request.POST.getlist('question[]')

        try:
            question_data = []

            for index, question_text in enumerate(questions):
                question_text = question_text.strip()

                if not question_text:
                    continue

                question_id = question_ids[index]
                answers = request.POST.getlist(f'answer_{question_id}[]')
                correct_answer = request.POST.get(f'correct_answer_{question_id}')

                answers = [answer.strip() for answer in answers if answer.strip()]

                if len(answers) < 2:
                    raise ValueError('Each question needs at least two answers.')

                if not correct_answer:
                    raise ValueError('Please select the correct answer for every question.')

                question_data.append({
                    'question_text': question_text,
                    'answers': answers,
                    'correct_answer': correct_answer,
                })

            if not question_data:
                raise ValueError('Please add at least one question.')

            with transaction.atomic():

                exam = Exam.objects.create(
                    title=title,
                    created_by=request.user,
                    duration_minutes=int(duration),
                    total_marks=int(marks),
                    passing_marks=int(pass_marks),
                    total_questions=len(question_data),
                    status='draft',
                    scheduled_date=exam_date,
                    scheduled_time=exam_time,
                )

                for q_index, q_data in enumerate(question_data, start=1):

                    question = ExamQuestion.objects.create(
                        exam=exam,
                        question_text=q_data['question_text'],
                        order=q_index,
                    )

                    for answer_index, answer_text in enumerate(q_data['answers']):

                        option_letter = chr(65 + answer_index)

                        ExamOption.objects.create(
                            question=question,
                            option_text=answer_text,
                            is_correct=(option_letter == q_data['correct_answer']),
                        )

            messages.success(request, 'Exam saved successfully.')

        except Exception as e:
            messages.error(request, f'Exam not saved: {e}')

        return redirect('teacher_examinations')

    context = {
        'active_page': 'examinations',
        **get_user_context(request.user),
    }

    return render(request, 'core/teacher/teacher_examinations.html', context)

def send_direct_message_email(msg):
  "Sends an email notification for direct messages and replies (both roles)"
  try:
    sender_name = msg.sender.get_full_name() or msg.sender.username
    subject_prefix = "" if str(msg.subject).lower().startswith("re:") else "New message"

    html_message = f'''
      <div style="font-family: Arial, sans-serif;max-width:  600px; margin: 0 auto; border: 1px solid #e4e8f0; border-radius: 12px; overflow: hidden;">
        <div style="background: #1c5ebc; padding: 20px; text-align: center; color: white;">
          <h2 style="margin: 0;">{subject_prefix}{msg.subject}</h2>
        </div>
        <div style="padding: 20px; background: #f9fafb;">
          <p><strong>From</strong> {sender_name}</p>
          <div style="background: #fff; padding: 15px; border-left: 4px solid #1c5ebc; border-radius: 4px; margin-top: 10px; white-space: pre-wrap;">{msg.body}</div>
          {"<p style='color: #d97706; font-size: 12px; margin-top: 15px;'>Attachment included - login to view.</p>" if msg.attachment else ""}
          <br>
          <p style="font-size: 12px; color: #6b7280;">Please log in to your EduExam dashboard to view and reply.</p>
        </div>
      </div>
    '''
    send_mail(
      subject = f"{subject_prefix}{msg.subject}",
      message = f"From {sender_name}:\n\n{msg.body}",
      from_email=settings.DEFAULT_FROM_EMAIL,
      recipient_list = [msg.receiver.email],
      html_message=html_message,
      fail_silently=False,
    )
  except Exception as e:
    return JsonResponse({'status':'error', 'message': str(e)})


def handle_edit_message(request, ann_id):
  if request.method == 'POST':
    try:
      ann = Message.objects.get(id=ann_id, sender=request.user)
      subject = request.POST.get('subject', '').strip()
      body = request.POST.get('body', '').strip()
      if not subject or not body:
        return JsonResponse({'status':'error', 'message':'Subject and message are required.'})
      ann.subject = subject
      ann.body = body
      ann.save()
      return JsonResponse({'status': 'ok', 'message': 'Message update successfully.'})
    except Message.DoesNotExist:
      return JsonResponse({'status': 'error', 'message': 'Message not found or unauthorize.'})
  return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@login_required(login_url='/login_register/teacher')
def teacher_announcements(request):

  announcements = Announcement.objects.filter(teacher=request.user).order_by('-created_at')

  # Teacher sent messages
  sent_messages = Message.objects.filter(sender=request.user, parent__isnull=True).prefetch_related('replies').order_by('-created_at')

  # Student inbox messages to Teacher
  inbox_messages = Message.objects.filter(receiver=request.user, parent__isnull=True).prefetch_related('replies').order_by('-created_at')

  teacher=request.user
  courses=Course.objects.filter(teacher=teacher)
  students = User.objects.filter(profile__role='student', enrolled_courses__in=courses).distinct()

  # Student messages inbox
  unread_count = inbox_messages.filter(is_read=False).count()
  context = {
    'active_page': 'announcements',
    'announcements': announcements,
    'courses': courses,
    'sent_messages': sent_messages,
    'inbox_messages': inbox_messages,
    'students': students,
    'unread_count': unread_count,
    'total': announcements.count(),
    'total_ann': announcements.filter(type='announcement').count(),
    'total_asgn': announcements.filter(type='assignment').count(),
    **get_user_context(request.user),
  }
  return render(request, 'core/teacher/teacher_announcements.html', context)

# Create Announcement
@login_required(login_url='/login_register/teacher')
def teacher_send_announcement(request):
  if request.method == 'POST':
    try:
      title=request.POST.get('title','').strip()
      message = request.POST.get('message', '').strip()
      ann_type = request.POST.get('type', 'announcement')
      priority = request.POST.get('priority', 'medium')
      course_id = request.POST.get('course_id')
      due_date_str = request.POST.get('due_date')
      due_date = None
      if due_date_str:
        from datetime import datetime
        try:
          due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
          return JsonResponse({
            'status': 'error',
            'message': 'Invalid due date format.'
          })

      if not title or not message:
        return JsonResponse({'status':'error','message':'Title and message fields are required.'})

      if ann_type == "assignment" and due_date is None:
        return JsonResponse({'status': 'error', 'message': 'Due date is required.'})

      # Get course
      course=None
      if course_id:
        course=Course.objects.filter(id=course_id, teacher=request.user).first()

      # Create Announcement
      announcement=Announcement.objects.create(title=title,message=message,type=ann_type,priority=priority,teacher=request.user,course=course,due_date=due_date,)

      ActivityLog.objects.create(
          user=request.user,
          action_type='announcement',
          description=f'Posted announcement "{announcement.title}"'
      )

      if course:
        student = course.students.all()
      else:
        teacher_courses = Course.objects.filter(teacher=request.user)

      # Handle attachment
      if 'attachment' in request.FILES:
        file = request.FILES['attachment']
        if file.size > 10 * 1024 * 1024:
          announcement.delete()
          return JsonResponse({'status': 'error', 'message': 'File too large. Max 10MB allowed.'})
        announcement.attachment = file
        announcement.save()

      # Send mail to all enrolled students
      email_count=send_announcement_email(announcement,course)

      return JsonResponse({'status':'ok','message':f'{"Assignment" if ann_type=="assignment" else "Announcement"} posted! Email sent to {email_count} students.'})

    except Exception as e:
      return JsonResponse({'status':'error','message':str(e)})
  return JsonResponse({'status':'error','message':'Invalid request.'})

def send_announcement_email(announcement, course):
  try:
    is_assignment = (announcement.type == 'assignment')
    sender_name = announcement.teacher.get_full_name() or announcement.teacher.username
    course_name = announcement.course.name if announcement.course else 'All Courses'
    posted_date = announcement.created_at.strftime('%d %B %Y, %I:%M %p')

    # Get all students
    if is_assignment:
      header_color = '#d97706'
      header_title = 'New Assignment'
      header_sub = 'You have a new assignment'
      type_label = 'Assignment'
      email_subject = f'New Assignment: {announcement.title} - EduExam'
      btn_color = '#d97706'

    else:
      header_color = '#1c5ebc'
      header_title = 'New Announcement'
      header_sub = 'Your teacher has posted a new announcement'
      type_label = 'Announcement'
      email_subject = f'Announcement: {announcement.title} - EduExam'
      btn_color = '#1c5ebc'

    due_date_html = ''
    msg_body_html = announcement.message.replace('\n', '<br>')
    if is_assignment and announcement.due_date:
      due_str = announcement.due_date.strftime('%d %B %Y, %I:%M %p')
      due_date_html = f'''
        <div style="background:#fee2e2;border-radius:8px;padding:10px 14px;font-size:13px;font-weight:600;color: #dc2626;margin-bottom:18px;">
          Due Date: {due_str}
        </div>
      '''



    # Build email content
    # HTML email version
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; background: #f4f6fa; margin: 0; padding: 20px;}}
        .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: {"#1c5ebc" if not is_assignment else "#d97706"}; padding: 28px 30px; text-align: center; }}
        .header h1 {{ color: #fff; margin: 0; font-size: 22px; }}
        .header p {{ color: rgba(255,255,255,.85); margin: 6px 0 0; font-size: 14px; }}
        .body {{ padding: 28px 30px }}
        .type-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; margin-bottom: 14px; background: {"#e8f0fb" if not is_assignment else "#fef3c7"}; color: {"#1c5ebc" if not is_assignment else "#d97706"}; }}
        .title {{ font-size: 20px; font-weight: 700; color: #1a1d2e; margin-bottom: 14px; }}
        .message {{ font-size: 14px; color: #374151; line-height: 1.7; background: #f9fafb; border-left: 4px solid {"#1c5ebc" if not is_assignment else "#d97706"}; padding: 16px; border-radius: 0 8px 8px 0; margin-bottom: 20px; }}
        .meta-row {{display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }}
        .meta-item {{font-size: 13px; color: #6b7280; }}
        .meta-item strong {{color: #1a1d2e; display: block; font-size: 12px; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 3px; }}
        .btn {{display: inline-block; background: #1c5ebc; color: #fff !important; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; }}
        .footer {{background: #f4f6fa; padding: 20px 30px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e4e8f0; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>{header_title}</h1>
          <p>{header_sub}</p>
        </div>
        <div class="body">
          <div class="type-badge">{type_label}</div>
          <div class="title">{announcement.title}</div>
          <div class="message">{msg_body_html}</div>
          {due_date_html}
          <div class="meta-row">
            <div class="meta-item">
              <strong>Course</strong>
              {course_name}
            </div>
            <div class="meta-item">
              <strong>Teacher</strong>
              {sender_name}
            </div>
            <div class="meta-item">
              <strong>Posted</strong>
              {posted_date}
            </div>
          </div>
          <a href="http://127.0.0.1:8000/student/announcements/" class="btn">View in EduExam Portal</a>
        </div>
        <div class="footer">
          EduExam - Online Examination &amp; Education System<br>
          You received because you are enrolled in a course
        </div>
      </div>
    </body>
    </html>
    '''

    # Plain text version
    plain_message = f'''
    Hello Student,
    New {type_label} from {sender_name}

    {"=" * 50}
    {announcement.title.upper()}
    {"=" * 50}

    {announcement.message}


    Course: {course_name}
    Teacher: {sender_name}
    Posted: {posted_date}

    Please login to EduExam to view full details.

    Best regards,
    EduExam Team
    '''
    if course:
      students = course.students.filter(profile__is_verified=True)
    else:
      # All students enrolled in teacher's courses
      teacher_courses = Course.objects.filter(teacher=announcement.teacher)
      students = User.objects.filter(enrolled_courses__in=teacher_courses).distinct()



    # Send mail to all students
    recipient_list = [s.email for s in students if s.email]

    if recipient_list:
      send_mail(
        subject = email_subject,
        message = plain_message,
        from_email = settings.DEFAULT_FROM_EMAIL,
        recipient_list = recipient_list,
        html_message = html_message,
        fail_silently = False,
      )
      return len(recipient_list)

  except Exception as e:
    print(f"Email error: {e}")
    return 0

# Delete Announcement
@login_required(login_url='/login_register/teacher')
def teacher_delete_announcement(request, ann_id):
  if request.method == 'POST':
    try:
      ann = Announcement.objects.get(id=ann_id, teacher=request.user)
      ann.delete()
      return JsonResponse({'status':'ok','message':'Deleted Successfully'})
    except Announcement.DoesNotExist:
      try:
        msg = Message.objects.get(id=ann_id, sender=request.user)
        msg.delete()
        return JsonResponse({'status': 'ok', 'message': 'Message deleted'})
      except Message.DoesNotExist:
        return JsonResponse({'status':'error','message':'Not found'})
  return JsonResponse({'status':'error','message':'Invalid request.'})


@login_required(login_url='/login_register/teacher')
def teacher_view_announcement(request, ann_id):
  try:
    msg = Message.objects.get(id=ann_id, receiver=request.user)
    msg.is_read = True
    msg.save()
    return JsonResponse({
        'status': 'ok',
        'subject': msg.subject,
        'body': msg.body,
        'sender': msg.sender.get_full_name() or msg.sender.username,
        'sender_email': msg.sender.email,
        'sender_id': msg.sender.id,
        'created_at': msg.created_at.strftime('%d %B %Y, %I:%M %p'),
        'attachment_name': msg.get_attachment_name(),
        'attachment_url': msg.attachment.url if msg.attachment else None,
        'attachment_size': msg.get_attachment_size(),
    })
  except Message.DoesNotExist:
    return JsonResponse({'status':'error', 'message':'Message not found.'})


# Teacher reply to student message
@login_required(login_url='/login_register/teacher')
def teacher_reply_message(request, ann_id):
  if request.method == 'POST':
    try:
      parent_msg = Message.objects.get(id=ann_id)
      body=request.POST.get('body', '').strip()
      attachment = request.FILES.get("attachment")
      if not body:
        return JsonResponse({'status':'error','message':'Reply cannot be empty.'})

      # Save attachment if provided
      if attachment:
        if attachment.size > 10 * 1024 * 1024:
          return JsonResponse({'status': 'error', 'message': 'File too large.'})

      reply = Message.objects.create(
        sender=request.user,
        receiver=parent_msg.sender,
        subject=f"Re: {parent_msg.subject}",
        body=body,
        attachment=attachment,
        parent = parent_msg
      )

      parent_msg.is_read = True
      parent_msg.save()

      send_direct_message_email(parent_msg)

      return JsonResponse({'status': 'ok', 'message': 'Message sent!'})
    except Message.DoesNotExist:
      return JsonResponse({'status': 'error', 'message': 'Original message not found'})
    except Exception as e:
      return JsonResponse({'status': 'error', 'message': str(e)})
  return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

@login_required(login_url='/login_register/teacher')
def teacher_students(request):
  courses = Course.objects.filter(teacher=request.user)

  # Build student data across all teacher's courses
  student_data = []
  seen = {}

  for course in courses:
    for student in course.students.all():
      prog = CourseProgress.objects.filter(
          student=student, course=course).first()
      progress = prog.progress if prog else 0

      if student.id not in seen:
        seen[student.id] = {
            'user': student,
            'email': student.email,
            'profile': student.profile,
            'courses': []
        }
      seen[student.id]['courses'].append({
          'name': course.name,
          'progress': progress,
      })

  student_data = list(seen.values())

  context = {
      'active_page': 'students',
      'student_data': student_data,
      'total_students': len(student_data),
      'total_courses': courses.count(),
      **get_user_context(request.user),
  }
  return render(request, 'core/teacher/teacher_students.html', context)

from django.contrib.auth.decorators import login_required
from .models import StudentExamAttempt

@login_required(login_url='/login_register/teacher/')
def teacher_results(request):

    results = StudentExamAttempt.objects.select_related(
        "student",
        "exam"
    ).order_by("-submitted_at")

    return render(request, "core/teacher/teacher_results.html", {
        "results": results,
    })


@login_required(login_url='/login_register/teacher')
def teacher_profile(request):
  profile = request.user.profile
  context = {
      'active_page': 'profile',
      'profile': profile,
      'email': request.user.email,
      **get_user_context(request.user),
  }
  return render(request, 'core/teacher/teacher_profile.html', context)


# ------------------- Course Player -------------------
@login_required(login_url='/login_register/student')
def course_player(request, course_id):
  try:
    course = Course.objects.get(id=course_id)

    if not course.students.filter(id=request.user.id).exists():
      messages.error(request, "You must be enrolled to access this course.")
      return redirect('student_courses')

    progress, created = CourseProgress.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'progress': 0}
    )

    context = {
        'active_page': 'courses',
        'course': course,
        'progress': progress,
        'resources': course.resources.all(),
        **get_user_context(request.user),
    }
    return render(request, 'core/student/student_courseplayer.html', context)

  except Course.DoesNotExist:
    messages.error(request, "Course not found.")
    return redirect('student_courses')


# ------------------- Course Progress -------------------
# ------------------- Course Progress -------------------
@login_required(login_url='/login_register/student')
def update_course_progress(request, course_id):
  if request.method == 'POST':
    try:
      import json
      data = json.loads(request.body)
      new_progress = int(data.get('progress', 0))

      progress, created = CourseProgress.objects.get_or_create(
          student=request.user,
          course_id=course_id,
          defaults={'progress': new_progress}
      )

      if not created:
        progress.progress = new_progress
        progress.save()

      if new_progress >= 100:
        Course.objects.filter(id=course_id).update(status='completed')

      return JsonResponse({'status': 'ok', 'progress': new_progress})
    except Exception as e:
      return JsonResponse({'status': 'error', 'message': str(e)})

  return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# ------------------- Login -------------------
# ------------------- Login -------------------
def insert_login(request, role):
  if request.method != "POST":
    return redirect('home')

  is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

  if role == 'student' and not getattr(settings, 'STUDENT_LOGIN_ENABLED', True):
    msg = 'Student login is currently disabled.'
    if is_ajax:
      return JsonResponse({
          'status': 'error',
          'message': msg,
          'timestamp': datetime.datetime.now().isoformat()
      })
    messages.error(request, msg)
    return render(request, 'core/login_register.html', {'role': 'student'})

  login_id = request.POST.get('lusername', '').strip()
  password = request.POST.get('lpassword', '').strip()

  if role == 'teacher':
    teacher = User.objects.select_related('profile').filter(
        username=login_id,
        profile__role='teacher'
    ).first()

    if teacher and teacher.check_password(password):
      if not teacher.profile.is_verified:
        return redirect('verify_otp_page', username=teacher.username)

      if not getattr(teacher.profile, 'admin_approved', False):
        messages.error(request, "Please wait for admin approval")
        return redirect('auth_page', role=role)

  user = authenticate(request, username=login_id, password=password)

  if user is None:
    messages.error(request, "Invalid username or password. Please try again")
    return redirect('auth_page', role=role)

  if user.profile.role != role:
    messages.error(
        request, f"Invalid Role: You are registered as a {user.profile.role}")
    return redirect('auth_page', role=role)

  if role == 'teacher' and not user.profile.is_verified:
    return redirect('verify_otp_page', username=user.username)

  if role == 'teacher' and not getattr(user.profile, 'admin_approved', False):
    messages.error(request, "Please wait for admin approval")
    return redirect('auth_page', role=role)

  login(request, user)

  ActivityLog.objects.create(
      user=user,
      action_type='login',
      description='Logged into the system'
  )

  next_url = request.POST.get("next") or request.GET.get("next")

  if next_url:
    return redirect(next_url)

  if role == "student":
    return redirect("student_dashboard")

  if role == "teacher":
    return redirect("teacher_dashboard")

  return redirect('home')

# ------------------- Register -------------------


def insert_register(request, role):
    if request.method != "POST":
      return redirect('auth_page', role=role)

    full_name = (request.POST.get('rusername') or '').strip()
    email = (request.POST.get('remail') or '').strip().lower()
    password = request.POST.get('rpassword') or ''
    confirm_password = request.POST.get('cpassword') or ''
    dob = request.POST.get('dob')
    roll_number = (request.POST.get('roll_number') or '').strip()
    teacher_id = (request.POST.get('teacher_id') or '').strip()

    unique_id = roll_number if role == "student" else teacher_id

    # Validation
    if not unique_id:
        messages.error(request, f"Please provide your {role} ID.")
        return redirect('auth_page', role=role)

    if len(password) < 8:
        messages.error(request, "Password must be at least 8 characters long.")
        return redirect('auth_page', role=role)

    if password != confirm_password:
        messages.error(request, "Passwords do not match.")
        return redirect('auth_page', role=role)

    if not email:
        messages.error(request, "Email is required.")
        return redirect('auth_page', role=role)

    if User.objects.filter(email=email).exists():
        messages.error(request, "This email is already registered.")
        return redirect('auth_page', role=role)

    if User.objects.filter(username=unique_id).exists():
        messages.error(request, "This ID is already registered.")
        return redirect('auth_page', role=role)

    try:
        with transaction.atomic():
            # Create inactive user
            user = User.objects.create_user(
                username=unique_id,
                email=email,
                password=password,
                first_name=full_name,
            )
            user.is_active = False
            user.save()

            # Delete any broken profile
            Profile.objects.filter(user=user).delete()

            # Create Profile
            profile = Profile.objects.create(
                user=user,
                role=role,
                dob=dob,
                roll_number=roll_number if role == "student" else None,
                teacher_id=teacher_id if role == "teacher" else None,
                is_verified=False,
            )

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            profile.otp = otp
            profile.otp_created_at = timezone.now()
            profile.otp_attempts = 0
            profile.save()

            # Send OTP Email
            send_mail(
                "EduExam - Email Verification OTP",
                f"Your OTP is: {otp}\nIt is valid for 2 minutes.",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            if role == 'student':
              success_msg = "Registration successful!"
              json_msg = "Registration successful!"
            else:  # teacher
              success_msg = "Registration successful! Waiting for admin approval."
              json_msg = "Registration successful! Please wait for admin approval."

            messages.success(request, success_msg)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "status": "success",
                    "message": json_msg,
                    "redirect_url": reverse('verify_otp_page', kwargs={'username': unique_id}),
                    'timestamp': datetime.datetime.now().isoformat()
                })

            return redirect('verify_otp_page', username=unique_id)

    except Exception as e:
        messages.error(request, f"Registration failed: {str(e)}")
        return redirect('auth_page', role=role)

# ------------------- Verify OTP -------------------

def ajax_verify_otp(request):
  if request.method=="POST":
    username = request.POST.get("username")
    entered_otp = request.POST.get("otp")

    try:
      user = User.objects.get(username=username)
      profile = user.profile

      #Expiry check
      if profile.is_otp_expired():
        user.delete()
        return JsonResponse({
          "status": "expired",
          "message": "OTP expired. Please register again."
        })

      #Max attempts
      if profile.otp_attempts >=3:
        user.delete()
        return JsonResponse({
          "status": "blocked",
          "message": "Too many wrong attempts. Try again later"
        })

      if entered_otp == profile.otp:
        profile.is_verified = True
        profile.otp = None
        profile.otp_created_at = None
        profile.otp_attempts = 0
        profile.save()

        user.is_active = True
        user.save()

        if profile.role == 'teacher':
          # Teachers still need admin approval
          user.is_active = False
          user.save()
          profile.admin_approved = False
          profile.save()

          return JsonResponse({
            "status": "success",
            "message": "Email verified! Waiting for admin approval.",
            "redirect_url": "/auth/teacher/"
          })

        # Students can login immediately after OTP
        return JsonResponse({
        "status": "success",
        "message": "Email verified successfully! You can now login.",
        "redirect_url": "/auth/student/"
      })
      else:
        profile.otp_attempts +=1
        profile.save()

      return JsonResponse({
        "status": "error",
        "message": "Invalid OTP."
      })

    except User.DoesNotExist:
      return JsonResponse({
        "status": "error",
        "message": "User not found."
      })


# ------------------- Resend OTP -------------------

def resend_otp(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # Now accept from frontend
        if not username:
            return JsonResponse({'success': False, 'message': 'Username required.'})

        try:
            user = User.objects.get(username=username)
            profile = user.profile

            # Generate fresh OTP
            new_otp = str(random.randint(100000, 999999))

            # Save to profile (works for both normal register + forgot)
            profile.otp = new_otp
            profile.otp_created_at = timezone.now()
            profile.otp_attempts = 0
            profile.save()

            # Send email
            if hasattr(request, 'session') and request.session.get('user_email'):
                email = request.session.get('user_email')
            else:
                email = user.email

            subject = "Your New Security Code"
            message = f"Your new One Time Password is: {new_otp}. It is valid for 2 minutes."

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            return JsonResponse({
                'success': True,
                'message': 'New OTP sent successfully to your email.'
            })

        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found.'})
        except Exception as e:
            print(f"Resend OTP error: {e}")
            return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def verify_otp_page(request, username):
  return render(request, "core/verify_otp.html", {"username": username})


def forgot_password(request):
  if request.method=="POST":
    email=request.POST.get("email",'').strip()
    # Check if email exists
    try:
      user=User.objects.get(email=email)
    except User.DoesNotExist:
      messages.error(request,'No account found with this email. Please enter your registered email.')
      return render(request,'core/forgot_password.html')

    # Check if email is verified
    if not user.profile.is_verified:
      messages.error(request,'This email is not verified. Please complete registration first.')
      return render(request,'core/forgot_password.html')

    # Generate OTP and save
    otp = str(random.randint(100000, 999999))
    user.profile.otp = otp
    user.profile.otp_created_at = timezone.now()
    user.profile.otp_attempts = 0
    user.profile.save()

    send_mail(
      "Password Reset OTP",
      f"Your OTP to reset password is {otp}. It is valid for 2 minutes.",
      settings.EMAIL_HOST_USER,
      [email],
      fail_silently=False,
    )

    messages.success(request,f"OTP sent to {email}")
    # Redirect to same existing OTP Page
    return redirect('forgot_verify_otp',username=user.username)
  return render(request, 'core/forgot_password.html')


def forgot_verify_otp(request, username):
  # Reuse the same OTP page but pass a flag so we know it's for password reset
  return render(request, "core/verify_otp.html", {
    "username": username,
    "is_forgot_password":True # This flag changes redirect after verify
  })


def ajax_verify_forgot_otp(request):
  if request.method == "POST":
    username = request.POST.get("username")
    entered_otp = request.POST.get("otp")

    try:
      user = User.objects.get(username=username)
      profile = user.profile

      # Expiry check
      if profile.is_otp_expired():
        return JsonResponse({
          "status": "expired",
          "message": "OTP expired. Please request again."
        })

      # Max attempts
      if profile.otp_attempts >= 3:
        return JsonResponse({
          "status": "blocked",
          "message": "Too many wrong attempts. Try again later"
        })

      # Correct OTP
      if entered_otp == profile.otp:
        profile.otp = None
        profile.otp_created_at = None
        profile.otp_attempts=0
        profile.save()

        return JsonResponse({
          "status": "success",
          "message": "OTP verified",
          "redirect_url": f"/reset-password/{user.username}/"
        })
      else:
        profile.otp_attempts += 1
        profile.save()

        return JsonResponse({
          "status": "error",
          "message": "Invalid OTP."
        })

    except User.DoesNotExist:
      return JsonResponse({
        "status": "error",
        "message": "User not found."
      })


def reset_password(request,username):
  try:
    user=User.objects.get(username=username)
  except User.DoesNotExist:
    return redirect('home')

  if request.method == "POST":
    password = request.POST.get("password")
    confirm_password = request.POST.get("confirm_password")
    if len(password)<8:
      messages.error(request,'Password must be at least 8 characters.')
      return render(request,'core/reset_password.html',{'username':username})

    if password!=confirm_password:
      messages.error(request, 'Passwords do not match.')
      return render(request,'core/reset_password.html',{'username': username})

    # Update password
    user.set_password(password)
    user.save()
    messages.success(request,'Password reset successfully! Please Login.')
    return redirect('auth_page',role=user.profile.role)
  return render(request,'core/reset_password.html',{'username':username})


@login_required(login_url='/login_register/teacher')
def mark_messages_read(request):
  if request.method == 'POST':
    Message.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})
  return JsonResponse({'status': 'error'}, status=400)


# --------------------- Admin Portal only -----------------------------

def admin_login(request):
  if request.method == 'POST':
    username = request.POST.get('username')
    password = request.POST.get('password')

    user = authenticate(
      request,
      username=username,
      password=password
    )
    if user is not None:
      try:
        if user.is_superuser:
          login(request, user)
          ActivityLog.objects.create(
              user=user,
              action_type='login',
              description='Logged into the system'
          )
          return redirect('admin_dashboard')
        messages.error(request, 'Only administrator can login here.')


      except:
        pass
    else:
      messages.error(request, 'Invalid username or password.')

  return render(request, 'core/admin/admin_login.html')


@login_required(login_url='/auth/admin')
def admin_dashboard(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    # 1. Base Metric Calculations
    total_users = Profile.objects.filter(
        role__in=['student', 'teacher']
    ).count()
    students = User.objects.filter(profile__role='student')
    teachers = User.objects.filter(profile__role='teacher')

    total_students = students.count()
    total_teachers = teachers.count()

    verified_users = User.objects.filter(profile__is_verified=True).count()
    inactive_users = total_users - verified_users
    active_students = students.filter(profile__is_verified=True).count()

    courses = Course.objects.all()
    total_courses = courses.count()
    active_courses = courses.filter(status='active').count()

    exams = Exam.objects.all()
    total_exams = exams.count()
    upcoming_exams = exams.filter(status='upcoming').count()

    # Recent Announcements - Use correct fields
    recent_announcements = AdminAnnouncement.objects.all(
    ).order_by('-created_at')[:4]

    # 2. Progress Bar Percentages
    def safe_pct(part, whole):
        return round((part / whole * 100)) if whole > 0 else 0

    context = {
        'active_page': 'dashboard',
        'fullname': request.user.get_full_name() or request.user.username,

        # Stats
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_exams': total_exams,
        'upcoming_exams': upcoming_exams,
        'verified_users': verified_users,

        # Recent Data
        'recent_users': User.objects.select_related('profile').exclude(profile__role='admin').order_by('-date_joined')[:5],
        'recent_courses': courses.select_related('teacher').order_by('-created_at')[:4],
        'recent_exams': exams.order_by('-scheduled_date')[:4],
        'recent_announcements': recent_announcements,

        **get_user_context(request.user),
    }
    return render(request, 'core/admin/admin_dashboard.html', context)


@login_required(login_url='/auth/admin')
def admin_analytics(request):
  # Security check: Ensure only admins can access this view
  if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
    messages.error(request, "Unauthorized access.")
    return redirect('home')
  now = timezone.localtime(timezone.now())
  current_year = now.year
  current_month = now.month
  month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

  # Total students: only verified active students
  total_students = Profile.objects.filter(
    role='student',
    is_verified=True,
    user__is_active=True
).count()

# Total teachers: only admin-approved active teachers
  total_teachers = Profile.objects.filter(
      role='teacher',
      is_verified=True
  ).count()

# New students this month
  new_students = Profile.objects.filter(
    role='student',
    is_verified=True,
    user__is_active=True,
    user__date_joined__gte=month_start,
).count()

# New teachers this month
  new_teachers = Profile.objects.filter(
      role='teacher',
      is_verified=True,
      user__date_joined__gte=month_start,
  ).count()

  pending_teacher_approvals = Profile.objects.filter(
    role='teacher',
    is_verified=True,
    admin_approved=False
  ).count()

  # 2. Course Statuses
  active_courses = Course.objects.filter(status='active').count()
  pending_courses = Course.objects.filter(status='pending').count()
  completed_courses = Course.objects.filter(status='completed').count()

  # 3. Course-Specific Analytics (Enrollment & Progress)
  # Using Django's 'annotate' safely calculates total students and avg progress per course in ONE database hit
  course_details = Course.objects.annotate(
    total_enrolled=Count('students', distinct=True),
    avg_progress=Avg('courseprogress__progress')
  ).values('name', 'status', 'total_enrolled', 'avg_progress').order_by('-total_enrolled')

  # 4. Examination Conducted Metrics
  # Assumes a "conducted" exam is marked as 'completed'
  exams_this_month = Exam.objects.filter(
    status='completed',
    scheduled_date__year=current_year,
    scheduled_date__month=current_month
  ).count()

  exams_this_year = Exam.objects.filter(
    status='completed',
    scheduled_date__year=current_year
  ).count()

  # Fetching historical data from the new summary model for charting
  monthly_exam_history = MonthlyAnalyticsSummary.objects.all().order_by('-year','-month')[:12]

  context = {
    'active_page': 'analytics',
    'current_month_name': now.strftime('%B'),
    'current_year': current_year,

    # User Data
    'total_students': total_students,
    'total_teachers': total_teachers,
    'new_students': new_students,
    'new_teachers': new_teachers,
    'pending_teacher_approvals': pending_teacher_approvals,

    # Course Data
    'active_courses': active_courses,
    'pending_courses': pending_courses,
    'completed_courses': completed_courses,
    'course_details': course_details,

    # Exam Data
    'exams_this_month': exams_this_month,
    'exams_this_year': exams_this_year,
    'monthly_exam_history': monthly_exam_history,
  }

  return render(request, 'core/admin/admin_analytics.html', context)


@login_required(login_url='/auth/admin')
def admin_teachers(request):
    """
    Shows two tabs:
      - Pending    : email-verified teachers waiting for admin approval
      - Approved   : fully approved teachers
    Also supports search, sort, per-page, and pagination.
    """
    tab = request.GET.get('tab', 'pending')    # pending | approved | rejected
    search = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '-date_joined')
    page_num = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 10))

    base_qs = (
        User.objects
        .select_related('profile')
        .filter(profile__role='teacher')
    )

    # ── Tab filter ────────────────────────────────────────────────────
    if tab == 'pending':
        qs = base_qs.filter(profile__is_verified=True,
                            profile__admin_approved=False)
    elif tab == 'rejected':
        qs = base_qs.filter(profile__is_verified=True, profile__admin_approved=False,
                            profile__rejection_reason__isnull=False)
    else:  # approved
        qs = base_qs.filter(profile__admin_approved=True, is_active=True)

    # ── Search ────────────────────────────────────────────────────────
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(profile__teacher_id__icontains=search)
        )

    # ── Sort ─────────────────────────────────────────────────────────
    allowed = {'-date_joined', 'date_joined',
               'first_name', '-profile__admin_approved_at'}
    qs = qs.order_by(sort if sort in allowed else '-date_joined')

    # ── Summary counts ────────────────────────────────────────────────
    all_teachers = base_qs
    total_teachers = all_teachers.count()
    pending_count = all_teachers.filter(
        profile__is_verified=True, profile__admin_approved=False,
        profile__rejection_reason__isnull=True
    ).count()
    approved_count = all_teachers.filter(
        profile__admin_approved=True, is_active=True).count()
    rejected_count = all_teachers.filter(
        profile__is_verified=True, profile__admin_approved=False,
        profile__rejection_reason__isnull=False
    ).count()
    unverified_count = all_teachers.filter(profile__is_verified=False).count()

    # ── Paginate ──────────────────────────────────────────────────────
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    # Approval logs for approved teachers (shown in quick-view via AJAX)
    context = {
        'active_page':     'teachers',
        'tab':             tab,
        'search':          search,
        'f_sort':          sort,
        'per_page':        per_page,

        'page_obj':        page_obj,
        'teachers':        page_obj.object_list,
        'paginator':       paginator,
        'page_range':      _smart_page_range(page_obj.number, paginator.num_pages),
        'total_results':   qs.count(),

        # Stat counts
        'total_teachers':  total_teachers,
        'pending_count':   pending_count,
        'approved_count':  approved_count,
        'rejected_count':  rejected_count,
        'unverified_count': unverified_count,

        **get_user_context(request.user),
    }
    return render(request, 'core/admin/admin_teachers.html', context)


# ──────────────────────────────────────────────────────────────────────
#  APPROVE TEACHER  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_approve_teacher(request, user_id):
    """POST /eduexam-admin/teacher/<id>/approve/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        teacher = User.objects.select_related('profile').get(
            id=user_id, profile__role='teacher'
        )
        p = teacher.profile

        p.admin_approved = True
        p.admin_approved_at = timezone.now()
        p.rejection_reason = None
        p.save()

        # Activate the Django user so login works
        teacher.is_active = True
        teacher.save()

        # Log the action
        try:
            from .models import TeacherApprovalLog
            TeacherApprovalLog.objects.create(
                teacher=teacher, admin=request.user, action='approved'
            )
        except Exception:
            pass

        _log_activity(
            request.user,
            f'<strong>{request.user.get_full_name() or request.user.username}</strong> '
            f'approved teacher <strong>{teacher.get_full_name() or teacher.username}</strong>',
            icon='person_check', color='green',
        )

        # Email teacher
        _send_teacher_approval_email(teacher, approved=True)

        return JsonResponse({
            'status':  'ok',
            'message': f'Teacher "{teacher.get_full_name() or teacher.username}" approved successfully. Email sent.',
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Teacher not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ──────────────────────────────────────────────────────────────────────
#  REJECT TEACHER  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_reject_teacher(request, user_id):
    """POST /eduexam-admin/teacher/<id>/reject/  body: {reason: '...'}"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        import json
        body = json.loads(request.body)
        reason = body.get('reason', '').strip()

        teacher = User.objects.select_related('profile').get(
            id=user_id, profile__role='teacher'
        )
        p = teacher.profile

        p.admin_approved = False
        p.rejection_reason = reason or 'No reason provided.'
        p.save()
        teacher.is_active = False
        teacher.save()

        try:
            from .models import TeacherApprovalLog
            TeacherApprovalLog.objects.create(
                teacher=teacher, admin=request.user,
                action='rejected', reason=reason,
            )
        except Exception:
            pass

        _log_activity(
            request.user,
            f'<strong>{request.user.get_full_name() or request.user.username}</strong> '
            f'rejected teacher <strong>{teacher.get_full_name() or teacher.username}</strong>',
            icon='person_off', color='red',
        )
        _send_teacher_approval_email(teacher, approved=False, reason=reason)

        return JsonResponse({
            'status':  'ok',
            'message': f'Teacher rejected. Email notification sent.',
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Teacher not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ──────────────────────────────────────────────────────────────────────
#  REVOKE APPROVED TEACHER  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_revoke_teacher(request, user_id):
    """POST /eduexam-admin/teacher/<id>/revoke/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        teacher = User.objects.select_related('profile').get(
            id=user_id, profile__role='teacher'
        )
        p = teacher.profile
        p.admin_approved = False
        p.admin_approved_at = None
        p.rejection_reason = 'Account access revoked by administrator.'
        p.save()
        teacher.is_active = False
        teacher.save()

        try:
            from .models import TeacherApprovalLog
            TeacherApprovalLog.objects.create(
                teacher=teacher, admin=request.user, action='revoked'
            )
        except Exception:
            pass

        _log_activity(
            request.user,
            f'<strong>{request.user.get_full_name() or request.user.username}</strong> '
            f'revoked access for teacher <strong>{teacher.get_full_name() or teacher.username}</strong>',
            icon='person_remove', color='orange',
        )

        return JsonResponse({'status': 'ok', 'message': 'Teacher access revoked.'})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Teacher not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ──────────────────────────────────────────────────────────────────────
#  TEACHER DETAIL  (AJAX GET)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_teacher_detail(request, user_id):
    """GET /eduexam-admin/teacher/<id>/detail/  — AJAX JSON for slide panel."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'AJAX only.'}, status=400)
    try:
        teacher = User.objects.select_related('profile').get(
            id=user_id, profile__role='teacher'
        )
        p = teacher.profile

        # Courses taught
        courses = list(
            Course.objects.filter(teacher=teacher)
            .values('id', 'name', 'status')
            .annotate(student_count=db_models.Count('students'))
        )

        # Approval logs
        try:
            from .models import TeacherApprovalLog
            logs = list(
                TeacherApprovalLog.objects
                .filter(teacher=teacher)
                .select_related('admin')
                .values(
                    'action', 'reason',
                    'created_at',
                    'admin__first_name', 'admin__last_name', 'admin__username'
                )[:5]
            )
            for l in logs:
                from django.utils.timesince import timesince
                l['time_ago'] = timesince(l['created_at']) + ' ago'
                l['created_at'] = l['created_at'].strftime(
                    '%d %b %Y, %I:%M %p')
                adm_name = (l['admin__first_name'] or '') + \
                    ' ' + (l['admin__last_name'] or '')
                l['admin_name'] = adm_name.strip() or l['admin__username']
        except Exception:
            logs = []

        return JsonResponse({
            'status':          'ok',
            'id':              teacher.id,
            'full_name':       teacher.get_full_name() or teacher.username,
            'username':        teacher.username,
            'email':           teacher.email,
            'teacher_id':      p.teacher_id or '—',
            'dob':             p.dob.strftime('%d %B %Y') if p.dob else '—',
            'is_active':       teacher.is_active,
            'is_verified':     p.is_verified,
            'admin_approved':  getattr(p, 'admin_approved', False),
            'admin_approved_at': p.admin_approved_at.strftime('%d %b %Y, %I:%M %p') if getattr(p, 'admin_approved_at', None) else '—',
            'rejection_reason': getattr(p, 'rejection_reason', None) or '',
            'date_joined':     teacher.date_joined.strftime('%d %B %Y, %I:%M %p'),
            'courses':         courses,
            'total_courses':   len(courses),
            'total_students':  sum(c.get('student_count', 0) for c in courses),
            'approval_logs':   logs,
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Teacher not found.'})


# ──────────────────────────────────────────────────────────────────────
#  DELETE TEACHER  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_delete_teacher(request, user_id):
    """POST /eduexam-admin/teacher/<id>/delete/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        teacher = User.objects.select_related('profile').get(
            id=user_id, profile__role='teacher'
        )
        name = teacher.get_full_name() or teacher.username
        teacher.delete()
        _log_activity(
            request.user,
            f'<strong>{request.user.get_full_name() or request.user.username}</strong> '
            f'deleted teacher <strong>{name}</strong>',
            icon='delete', color='red',
        )
        return JsonResponse({'status': 'ok', 'message': f'Teacher "{name}" deleted.'})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Teacher not found.'})


# ──────────────────────────────────────────────────────────────────────
#  HELPER: send approval / rejection email to teacher
# ──────────────────────────────────────────────────────────────────────
def _send_teacher_approval_email(teacher, approved: bool, reason: str = ''):
    """Send a plain-text email to the teacher about their approval status."""
    name = teacher.get_full_name() or teacher.username
    if approved:
        subject = '✅ Your EduExam Teacher Account Has Been Approved!'
        body = (
            f"Dear {name},\n\n"
            f"Great news! The EduExam administration team has reviewed and "
            f"approved your teacher account.\n\n"
            f"You can now log in to the EduExam platform using your registered "
            f"email and password.\n\n"
            f"Login here: {settings.SITE_URL}/auth/teacher/\n\n"
            f"Welcome aboard! 🎓\n\n"
            f"— EduExam Admin Team\n"
            f"  OEES Platform"
        )
    else:
        subject = '❌ Your EduExam Teacher Account Registration'
        body = (
            f"Dear {name},\n\n"
            f"We have reviewed your teacher account registration for EduExam "
            f"and unfortunately we are unable to approve it at this time.\n\n"
        )
        if reason:
            body += f"Reason: {reason}\n\n"
        body += (
            f"If you believe this is an error or have questions, please contact "
            f"the administrator.\n\n"
            f"— EduExam Admin Team\n"
            f"  OEES Platform"
        )
    try:
        send_mail(
            subject, body,
            settings.EMAIL_HOST_USER,
            [teacher.email],
            fail_silently=True,
        )
    except Exception:
        pass


def _send_admin_new_teacher_email(teacher, admin_emails: list):
    """Notify all admin-role users when a new teacher registers."""
    name = teacher.get_full_name() or teacher.username
    tid = getattr(teacher.profile, 'teacher_id', '—') or '—'
    subject = f'🔔 New Teacher Registration: {name} needs approval'
    body = (
        f"Hello Admin,\n\n"
        f"A new teacher has registered on the EduExam OEES platform "
        f"and is awaiting your approval.\n\n"
        f"  Name       : {name}\n"
        f"  Teacher ID : {tid}\n"
        f"  Email      : {teacher.email}\n"
        f"  Registered : {teacher.date_joined.strftime('%d %B %Y, %I:%M %p')}\n\n"
        f"Please log in to the admin panel to review and approve/reject "
        f"this account:\n"
        f"{settings.SITE_URL}/eduexam-admin/teachers/\n\n"
        f"— EduExam System"
    )
    try:
        send_mail(
            subject, body,
            settings.EMAIL_HOST_USER,
            admin_emails,
            fail_silently=True,
        )
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────
#  HELPER — log student action
# ──────────────────────────────────────────────────────────────────────
def _log_student_action(admin, student, action, detail=''):
    """Safe logging for student management actions"""
    try:
        from .models import ActivityLog
        ActivityLog.objects.create(
            user=admin,
            action_type='student_management',
            description=f'Admin {action} student "{student.get_full_name() or student.username}" {detail}'
        )
    except Exception as e:
        print(f"Logging error (non-critical): {e}")


# ──────────────────────────────────────────────────────────────────────
#  STUDENTS LIST
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_students(request):
    """
    Two tabs:
      recent   — newly registered (last 7 days), newest first
      all      — every student, searchable / filterable
    """
    tab = request.GET.get('tab', 'all')       # all | recent | suspended
    search = request.GET.get('q', '').strip()
    # all | active | inactive | suspended
    f_status = request.GET.get('status', 'all')
    f_course = request.GET.get('course', 'all')    # all | <course_id>
    sort = request.GET.get('sort', '-date_joined')
    page_num = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 15))

    # ── Base queryset ─────────────────────────────────────────────────
    base_qs = User.objects.select_related('profile').prefetch_related('enrolled_courses').filter(
        profile__role='student'
    )

    # ── Tab filter ────────────────────────────────────────────────────
    week_ago = timezone.now() - timezone.timedelta(days=7)
    if tab == 'recent':
        qs = base_qs.filter(date_joined__gte=week_ago)
    elif tab == 'suspended':
        qs = base_qs.filter(profile__is_suspended=True)
    else:
        qs = base_qs

    # ── Search ────────────────────────────────────────────────────────
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(profile__roll_number__icontains=search)
        )

    # ── Status filter ─────────────────────────────────────────────────
    if f_status == 'active':
        qs = qs.filter(is_active=True, profile__is_suspended=False)
    elif f_status == 'inactive':
        qs = qs.filter(is_active=False)
    elif f_status == 'suspended':
        qs = qs.filter(profile__is_suspended=True)

    # ── Course filter ─────────────────────────────────────────────────
    if f_course != 'all':
        try:
            qs = qs.filter(enrolled_courses__id=int(f_course))
        except (ValueError, TypeError):
            pass

    # ── Sort ─────────────────────────────────────────────────────────
    allowed_sorts = {
        '-date_joined', 'date_joined', 'first_name', 'username'
    }
    qs = qs.order_by(sort if sort in allowed_sorts else '-date_joined')

    # ── Summary counts ────────────────────────────────────────────────
    total_students = base_qs.count()
    active_students = base_qs.filter(
        is_active=True, profile__is_suspended=False).count()
    suspended_students = base_qs.filter(profile__is_suspended=True).count()
    new_this_week = base_qs.filter(date_joined__gte=week_ago).count()
    verified_students = base_qs.filter(profile__is_verified=True).count()
    enrolled_students = base_qs.filter(
        enrolled_courses__isnull=False).distinct().count()

    # ── All courses for filter dropdown ──────────────────────────────
    all_courses = Course.objects.order_by('name')

    # ── Paginate ──────────────────────────────────────────────────────
    paginator = Paginator(qs.distinct(), per_page)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        'active_page': 'students',
        'tab':         tab,
        'search':      search,
        'f_status':    f_status,
        'f_course':    f_course,
        'f_sort':      sort,
        'per_page':    per_page,

        'page_obj':      page_obj,
        'students':      page_obj.object_list,
        'paginator':     paginator,
        'page_range':    _smart_page_range(page_obj.number, paginator.num_pages),
        'total_results': qs.distinct().count(),

        # Stats
        'total_students':     total_students,
        'active_students':    active_students,
        'suspended_students': suspended_students,
        'new_this_week':      new_this_week,
        'verified_students':  verified_students,
        'enrolled_students':  enrolled_students,

        # For filter dropdown
        'all_courses': all_courses,

        **get_user_context(request.user),
    }
    return render(request, 'core/admin/admin_students.html', context)



# ──────────────────────────────────────────────────────────────────────
#  STUDENT DETAIL  (AJAX GET)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_student_detail(request, user_id):
    """GET /eduexam-admin/student/<id>/detail/  — AJAX JSON."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'AJAX only.'}, status=400)

    try:
        student = User.objects.select_related('profile').get(
            id=user_id, profile__role='student'
        )
        p = student.profile

        # Enrolled courses with progress
        enrolled = []
        for course in Course.objects.filter(students=student).select_related('teacher'):
            prog = CourseProgress.objects.filter(
                student=student, course=course
            ).first()
            enrolled.append({
                'id':       course.id,
                'name':     course.name,
                'teacher':  course.teacher.get_full_name() or course.teacher.username,
                'status':   course.status,
                'progress': prog.progress if prog else 0,
            })

        # Activity logs — safely wrapped
        logs = []
        try:
            from .models import StudentActivityLog
            for l in StudentActivityLog.objects.filter(student=student).select_related('admin')[:8]:
                logs.append({
                    'action':     getattr(l, 'get_action_display', lambda: l.action)(),
                    'detail':     getattr(l, 'detail', '') or '',
                    'admin_name': l.admin.get_full_name() or l.admin.username if l.admin else 'System',
                    'time_ago':   timesince(l.created_at) + ' ago',
                    'created_at': l.created_at.strftime('%d %b %Y, %I:%M %p'),
                    'action_key': getattr(l, 'action', 'info'),
                })
        except Exception as log_err:
            print(f"Activity log error (non-critical): {log_err}")
            logs = []

        return JsonResponse({
            'status':           'ok',
            'id':               student.id,
            'full_name':        student.get_full_name() or student.username,
            'first_name':       student.first_name,
            'last_name':        student.last_name,
            'username':         student.username,
            'email':            student.email,
            'roll_number':      getattr(p, 'roll_number', '—') or '—',
            'dob':              p.dob.strftime('%d %B %Y') if getattr(p, 'dob', None) else '—',
            'is_active':        student.is_active,
            'is_verified':      getattr(p, 'is_verified', False),
            'is_suspended':     getattr(p, 'is_suspended', False),
            'suspended_at':     p.suspended_at.strftime('%d %b %Y, %I:%M %p') if getattr(p, 'suspended_at', None) else None,
            'suspension_reason': getattr(p, 'suspension_reason', '') or '',
            'date_joined':      student.date_joined.strftime('%d %B %Y, %I:%M %p'),
            'enrolled_courses': enrolled,
            'total_courses':    len(enrolled),
            'activity_logs':    logs,
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found.'})
    except Exception as e:
        print(f"ERROR in admin_student_detail: {e}")  # For server logs
        return JsonResponse({'status': 'error', 'message': 'Server error loading profile.'}, status=500)

# ──────────────────────────────────────────────────────────────────────
#  EDIT STUDENT  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_edit_student(request, user_id):
    """POST /eduexam-admin/student/<id>/edit/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        student = User.objects.select_related('profile').get(
            id=user_id, profile__role='student'
        )
        p = student.profile

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name',  '').strip()
        email = request.POST.get('email',      '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        dob = request.POST.get('dob',        '').strip()
        is_active = request.POST.get('is_active',  'true') == 'true'

        if not first_name:
            return JsonResponse({'status': 'error', 'message': 'First name is required.'})
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email is required.'})
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already in use by another user.'})

        student.first_name = first_name
        student.last_name = last_name
        student.email = email
        student.is_active = is_active
        student.save()

        if roll_number:
            p.roll_number = roll_number
        if dob:
            from django.utils.dateparse import parse_date
            parsed = parse_date(dob)
            if parsed:
                p.dob = parsed
        p.save()

        _log_student_action(
            request.user, student, 'edited',
            f'Name: {first_name} {last_name}, Email: {email}'
        )
        return JsonResponse({'status': 'ok', 'message': 'Student updated successfully.'})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ──────────────────────────────────────────────────────────────────────
#  SUSPEND / UNSUSPEND  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_suspend_student(request, user_id):
    """POST /eduexam-admin/student/<id>/suspend/  body JSON: {reason}"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        import json
        body = json.loads(request.body)
        reason = body.get('reason', '').strip(
        ) or 'Suspicious activity detected.'

        student = User.objects.select_related('profile').get(
            id=user_id, profile__role='student'
        )
        p = student.profile

        p.is_suspended = True
        p.suspended_at = timezone.now()
        p.suspension_reason = reason
        p.save()

        student.is_active = False
        student.save()

        _log_student_action(request.user, student, 'suspended', reason)

        # Email student
        try:
            send_mail(
                '⚠️ Your EduExam Account Has Been Suspended',
                f"Dear {student.get_full_name() or student.username},\n\n"
                f"Your EduExam student account has been suspended by the administrator.\n\n"
                f"Reason: {reason}\n\n"
                f"If you believe this is an error, please contact the EduExam support team.\n\n"
                f"— EduExam Admin Team",
                settings.EMAIL_HOST_USER,
                [student.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return JsonResponse({
            'status':  'ok',
            'message': f'Student suspended. Email notification sent.',
            'is_suspended': True,
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@admin_required
def admin_unsuspend_student(request, user_id):
    """POST /eduexam-admin/student/<id>/unsuspend/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        student = User.objects.select_related('profile').get(
            id=user_id, profile__role='student'
        )
        p = student.profile
        p.is_suspended = False
        p.suspended_at = None
        p.suspension_reason = None
        p.save()

        student.is_active = True
        student.save()

        _log_student_action(request.user, student, 'unsuspended')

        try:
            send_mail(
                '✅ Your EduExam Account Has Been Restored',
                f"Dear {student.get_full_name() or student.username},\n\n"
                f"Your EduExam student account suspension has been lifted.\n"
                f"You can now log in and continue using the platform.\n\n"
                f"— EduExam Admin Team",
                settings.EMAIL_HOST_USER,
                [student.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return JsonResponse({
            'status':  'ok',
            'message': 'Student account restored. Email sent.',
            'is_suspended': False,
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found.'})


# ──────────────────────────────────────────────────────────────────────
#  TOGGLE ACTIVE  (lock / unlock without suspension)  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_toggle_student(request, user_id):
    """POST /eduexam-admin/student/<id>/toggle/"""
    try:
        student = User.objects.select_related('profile').get(
            id=user_id, profile__role='student'
        )
        student.is_active = not student.is_active
        student.save()

        action = 'unlocked' if student.is_active else 'locked'
        _log_student_action(request.user, student, action)

        return JsonResponse({
            'status': 'ok',
            'message': f'Student account {action}.',
            'is_active': student.is_active,
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# ──────────────────────────────────────────────────────────────────────
#  ENROLL / UNENROLL COURSE  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_student_enroll(request, user_id):
    """POST /eduexam-admin/student/<id>/enroll/  body: {course_id}"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        import json
        body = json.loads(request.body)
        course_id = body.get('course_id')
        student = User.objects.select_related(
            'profile').get(id=user_id, profile__role='student')
        course = Course.objects.get(id=course_id)

        if course.students.filter(id=user_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Already enrolled in this course.'})

        course.students.add(student)
        CourseProgress.objects.get_or_create(
            student=student, course=course, defaults={'progress': 0})
        _log_student_action(request.user, student, 'enrolled', course.name)
        return JsonResponse({'status': 'ok', 'message': f'Enrolled in "{course.name}".'})
    except (User.DoesNotExist, Course.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Student or course not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@admin_required
def admin_student_unenroll(request, user_id):
    """POST /eduexam-admin/student/<id>/unenroll/  body: {course_id}"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        import json
        body = json.loads(request.body)
        course_id = body.get('course_id')
        student = User.objects.select_related(
            'profile').get(id=user_id, profile__role='student')
        course = Course.objects.get(id=course_id)

        course.students.remove(student)
        CourseProgress.objects.filter(student=student, course=course).delete()
        _log_student_action(request.user, student, 'unenrolled', course.name)
        return JsonResponse({'status': 'ok', 'message': f'Unenrolled from "{course.name}".'})
    except (User.DoesNotExist, Course.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Student or course not found.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ──────────────────────────────────────────────────────────────────────
#  DELETE  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_delete_student(request, user_id):
    """POST /eduexam-admin/student/<id>/delete/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        student = User.objects.select_related('profile').get(
            id=user_id, profile__role='student'
        )
        name = student.get_full_name() or student.username
        _log_activity(
            request.user,
            f'<strong>{request.user.get_full_name() or request.user.username}</strong> '
            f'deleted student <strong>{name}</strong>',
            icon='delete', color='red',
        )
        student.delete()
        return JsonResponse({'status': 'ok', 'message': f'Student "{name}" deleted.'})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found.'})


# ──────────────────────────────────────────────────────────────────────
#  EXPORT CSV
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_export_students(request):
    """GET /eduexam-admin/students/export/"""
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="eduexam_students.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Full Name', 'Username', 'Roll Number', 'Email',
        'Date of Birth', 'Verified', 'Active', 'Suspended',
        'Suspension Reason', 'Enrolled Courses', 'Joined Date',
    ])
    for s in User.objects.select_related('profile').filter(profile__role='student').order_by('-date_joined'):
        p = s.profile
        courses = ', '.join(Course.objects.filter(
            students=s).values_list('name', flat=True))
        writer.writerow([
            s.get_full_name() or s.username,
            s.username,
            p.roll_number or '—',
            s.email,
            p.dob.strftime('%d %b %Y') if p.dob else '—',
            'Yes' if p.is_verified else 'No',
            'Yes' if s.is_active else 'No',
            'Yes' if getattr(p, 'is_suspended', False) else 'No',
            getattr(p, 'suspension_reason', '') or '',
            courses,
            s.date_joined.strftime('%d %b %Y'),
        ])
    _log_activity(request.user,
                  f'<strong>{request.user.get_full_name() or request.user.username}</strong> exported student list',
                  icon='download', color='teal')
    return response





@login_required(login_url='/auth/admin')
def admin_examinations(request):
  return render(request, 'core/admin/admin_examinations.html')


@login_required(login_url='/auth/admin')
def admin_results(request):
  return render(request, 'core/admin/admin_results.html')




@login_required(login_url='/auth/admin')
def admin_profile(request):
  return render(request, 'core/admin/admin_profile.html')


@login_required(login_url='/auth/admin')
def admin_reports(request):
  return render(request, 'core/admin/admin_reports.html')


@login_required(login_url='/auth/admin')
def admin_messages(request):
  return render(request, 'core/admin/admin_messages.html')



@login_required(login_url='/auth/admin')
def admin_users(request):
  # ── Query params ──────────────────────────────────────────────────
  search = request.GET.get('q', '').strip()
  # all | student | teacher | admin
  role = request.GET.get('role', 'all')
  status = request.GET.get('status', 'all')        # all | active | inactive
  verified = request.GET.get('verified', 'all')      # all | yes | no
  # date_joined | -date_joined | username | first_name
  sort = request.GET.get('sort', '-date_joined')
  page_num = request.GET.get('page', 1)
  per_page = int(request.GET.get('per_page', 10))    # 10 | 25 | 50

  # ── Base queryset ─────────────────────────────────────────────────
  qs = User.objects.select_related('profile').all()

  # ── Filters ───────────────────────────────────────────────────────
  if search:
    qs = qs.filter(
      Q(first_name__icontains=search) |
      Q(last_name__icontains=search) |
      Q(username__icontains=search) |
      Q(email__icontains=search) |
      Q(profile__roll_number__icontains=search) |
      Q(profile__teacher_id__icontains=search)
    )

  if role != 'all':
    qs = qs.filter(profile__role=role)

  if status == 'active':
    qs = qs.filter(is_active=True)
  elif status == 'inactive':
    qs = qs.filter(is_active=False)

  if verified == 'yes':
    qs = qs.filter(profile__is_verified=True)
  elif verified == 'no':
    qs = qs.filter(profile__is_verified=False)

  # ── Sort ──────────────────────────────────────────────────────────
  allowed_sorts = {
    'date_joined':  'date_joined',
    '-date_joined': '-date_joined',
    'username':     'username',
    'first_name':   'first_name',
  }
  qs = qs.order_by(allowed_sorts.get(sort, '-date_joined'))

  # ── Summary counts (always across all users, not filtered) ────────
  all_users = User.objects.select_related('profile')
  total_all = Profile.objects.filter(
    role__in=['student', 'teacher']
).count()
  total_students = all_users.filter(profile__role='student').count()
  total_teachers = all_users.filter(profile__role='teacher').count()
  total_active = all_users.filter(is_active=True).count()
  total_inactive = all_users.filter(is_active=False).count()
  total_verified = all_users.filter(profile__is_verified=True).count()

  # New this week
  week_ago = timezone.now() - timezone.timedelta(days=7)
  new_this_week = all_users.filter(date_joined__gte=week_ago).count()

  # ── Paginate ──────────────────────────────────────────────────────
  paginator = Paginator(qs, per_page)
  try:
    page_obj = paginator.page(page_num)
  except (PageNotAnInteger, EmptyPage):
    page_obj = paginator.page(1)

  # Build a smart page range (never more than 7 page buttons shown)
  total_pages = paginator.num_pages
  current_page = page_obj.number
  page_range = _smart_page_range(current_page, total_pages)

  context = {
    'active_page': 'users',

    # list
    'page_obj':      page_obj,
    'users':         page_obj.object_list,
    'paginator':     paginator,
    'page_range':    page_range,
    'total_results': qs.count(),

    # filters (echo back so template can re-select)
    'search':   search,
    'f_role':   role,
    'f_status': status,
    'f_verified': verified,
    'f_sort':   sort,
    'per_page': per_page,

    # summary stats
    'total_all':      total_all,
    'total_students': total_students,
    'total_teachers': total_teachers,
    'total_active':   total_active,
    'total_inactive': total_inactive,
    'total_verified': total_verified,
    'new_this_week':  new_this_week,

    **get_user_context(request.user),
  }
  return render(request, 'core/admin/admin_users.html', context)


def _smart_page_range(current, total, wing=2):
    """
    Returns a list of page numbers with None as ellipsis gaps.
    E.g.  [1, None, 4, 5, 6, None, 20]
    """
    pages = set()
    pages.add(1)
    pages.add(total)
    for p in range(max(1, current - wing), min(total, current + wing) + 1):
        pages.add(p)
    result = []
    prev = None
    for p in sorted(pages):
        if prev is not None and p - prev > 1:
            result.append(None)   # ellipsis
        result.append(p)
        prev = p
    return result


# ──────────────────────────────────────────────────────────────────────
#  DETAIL / QUICK-VIEW  (AJAX GET)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_user_detail(request, user_id):
    """
    GET /admin/user/<id>/detail/
    Returns JSON for the quick-view slide-over panel.
    """
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'AJAX only'}, status=400)
    try:
        u = User.objects.select_related('profile').get(id=user_id)
        p = u.profile
        enrolled = []
        if p.role == 'student':
            enrolled = list(
                Course.objects.filter(students=u).values(
                    'id', 'name', 'status')
            )
        teaching = []
        if p.role == 'teacher':
            teaching = list(
                Course.objects.filter(teacher=u).values('id', 'name', 'status')
            )
        return JsonResponse({
            'status':       'ok',
            'id':           u.id,
            'full_name':    u.get_full_name() or u.username,
            'username':     u.username,
            'email':        u.email,
            'role':         p.role,
            'roll_number':  p.roll_number or '',
            'teacher_id':   p.teacher_id or '',
            'dob':          p.dob.strftime('%d %B %Y') if p.dob else '—',
            'is_active':    u.is_active,
            'is_verified':  p.is_verified,
            'date_joined':  u.date_joined.strftime('%d %B %Y, %I:%M %p'),
            'enrolled':     enrolled,
            'teaching':     teaching,
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found.'})


# ──────────────────────────────────────────────────────────────────────
#  TOGGLE ACTIVE  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
@require_http_methods(["POST"])
def admin_user_toggle(request, user_id):
    """POST /admin/user/<id>/toggle/"""
    try:
        target = User.objects.select_related('profile').get(id=user_id)

        if target == request.user:
            return JsonResponse({'status': 'error', 'message': 'Cannot deactivate yourself.'})

        target.is_active = not target.is_active
        target.save()

        state = 'activated' if target.is_active else 'deactivated'

        # FIXED: Changed undefined 'name' to target.get_full_name() or target.username
        target_name = target.get_full_name() or target.username
        ActivityLog.objects.create(
            user=request.user,
            action_type='user_management',
            description=f'Admin {state} account for user "{target_name}"'
        )

        return JsonResponse({
            'status': 'ok',
            'message': f'User {state} successfully.',
            'is_active': target.is_active,
        })

    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found.'})


# ──────────────────────────────────────────────────────────────────────
#  GLOBAL STUDENT LOGIN CONTROL
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_toggle_student_login(request):
    """POST /eduexam-admin/toggle-student-login/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

    try:
        import json
        data = json.loads(request.body)
        activate = data.get('activate', True)

        from django.conf import settings
        settings.STUDENT_LOGIN_ENABLED = activate

        status = "activated" if activate else "deactivated"

        _log_activity(
            request.user,
            f'Student login globally {status}',
            icon='login' if activate else 'lock',
            color='green' if activate else 'red'
        )

        if not activate:
            # Notify students
            students = User.objects.filter(
                profile__role='student', is_active=True)
            for student in students:
                try:
                    send_mail(
                        '🔴 EduExam Maintenance Notice',
                        f"Dear Student,\n\n"
                        f"Student login has been temporarily **disabled** by the administrator.\n"
                        f"The site is under maintenance.\n\n"
                        f"We will notify you when login is restored.\n\n"
                        f"Thank you,\nEduExam Admin",
                        settings.DEFAULT_FROM_EMAIL,
                        [student.email],
                        fail_silently=True,
                    )
                except:
                    pass

        return JsonResponse({
            'status': 'ok',
            'message': f'Student login has been {status}.',
            'enabled': activate
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

# ──────────────────────────────────────────────────────────────────────
#  DELETE  (POST)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_user_delete(request, user_id):
    """POST /admin/user/<id>/delete/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        target = User.objects.select_related('profile').get(id=user_id)
        if target == request.user:
            return JsonResponse({'status': 'error', 'message': 'Cannot delete yourself.'})
        name = target.get_full_name() or target.username
        target.delete()
        ActivityLog.objects.create(
          user=request.user,
          action_type='user_management',
          description=f'Admin deleted user "{name}"'
        )
        return JsonResponse({'status': 'ok', 'message': f'User "{name}" deleted successfully.'})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found.'})


# ──────────────────────────────────────────────────────────────────────
#  EDIT  (POST)  — name, email, role, status
# ──────────────────────────────────────────────────────────────────────
@admin_required
@require_http_methods(["POST"])
def admin_user_edit(request, user_id):
    """POST /admin/user/<id>/edit/"""
    try:
        print("User:", request.user.username)
        print("Superuser:", request.user.is_superuser)
        print("Role:", request.user.profile.role)

        target = User.objects.select_related('profile').get(id=user_id)
        p = target.profile

        # Retrieve information sent via FormData or POST body
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        new_role = request.POST.get('role', p.role).strip()
        is_active = request.POST.get('is_active', 'true') == 'true'

        if not first_name:
            return JsonResponse({'status': 'error', 'message': 'First name is required.'})
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email is required.'})

        # Email uniqueness check (excluding self)
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already in use by another user.'})

        # Save target attributes
        target.first_name = first_name
        target.last_name = last_name
        target.email = email
        target.is_active = is_active
        target.save()

        if new_role in ('student', 'teacher'):
            p.role = new_role
            p.save()

        # FIXED: Changed undefined 'name' to target.get_full_name() or target.username
        target_name = target.get_full_name() or target.username
        ActivityLog.objects.create(
            user=request.user,
            action_type='user_management',
            description=f'Admin updated details for user "{target_name}"'
        )

        return JsonResponse({'status': 'ok', 'message': 'User updated successfully.'})

    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found.'})

# ──────────────────────────────────────────────────────────────────────
#  BULK DELETE  (POST)  — body: {"ids": [1, 2, 3]}
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_users_bulk_delete(request):
    """POST /admin/users/bulk-delete/"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    import json
    try:
        body = json.loads(request.body)
        ids = [int(i) for i in body.get('ids', []) if str(i).isdigit()]
        # Never delete the requesting admin
        ids = [i for i in ids if i != request.user.id]
        count = User.objects.filter(id__in=ids).count()
        User.objects.filter(id__in=ids).delete()
        ActivityLog.objects.create(
            user=request.user,
            action_type='user_management',
            description=f'Admin deleted user "{name}"'
        )
        return JsonResponse({'status': 'ok', 'message': f'{count} user(s) deleted.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ──────────────────────────────────────────────────────────────────────
#  EXPORT CSV  (GET)
# ──────────────────────────────────────────────────────────────────────
@admin_required
def admin_users_export(request):
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="eduexam_users.csv"'

    writer = csv.writer(response)
    writer.writerow(['Full Name', 'Username', 'Email', 'Role', 'Roll No / Teacher ID',
                    'Date of Birth', 'Active', 'Verified', 'Joined Date'])

    users = User.objects.select_related('profile').exclude(
        profile__role='admin').exclude(is_superuser=True).order_by('-date_joined')

    for u in users:
        p = u.profile
        id_val = p.roll_number if p.role == 'student' else (
            p.teacher_id or '—')
        writer.writerow([
            u.get_full_name() or u.username,
            u.username,
            u.email,
            p.role.capitalize(),
            id_val,
            p.dob.strftime('%d %b %Y') if p.dob else '—',
            'Yes' if u.is_active else 'No',
            'Yes' if p.is_verified else 'No',
            u.date_joined.strftime('%d %b %Y'),
        ])
    return response


# ====================== ADMIN COURSE MANAGEMENT ======================
@admin_required
@login_required(login_url='/auth/admin')
def admin_courses(request):
    tab = request.GET.get('tab', 'pending')
    search = request.GET.get('q', '').strip()

    qs = Course.objects.select_related('teacher', 'teacher__profile')

    if tab == 'pending':
        qs = qs.filter(status='pending')
    elif tab == 'approved':
        qs = qs.filter(status='approved')
    elif tab == 'rejected':
        qs = qs.filter(status='rejected')
    else:
        qs = qs.filter(status='draft')

    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(teacher__first_name__icontains=search) |
            Q(teacher__last_name__icontains=search)
        )

    context = {
        'active_page': 'courses',
        'tab': tab,
        'search': search,
        'courses': qs.order_by('-created_at'),
        'total_pending': Course.objects.filter(status='pending').count(),
        'total_approved': Course.objects.filter(status='approved').count(),
        'total_rejected': Course.objects.filter(status='rejected').count(),
        **get_user_context(request.user),
    }
    return render(request, 'core/admin/admin_courses.html', context)


@admin_required
def admin_approve_course(request, course_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        course = Course.objects.select_related('teacher').get(id=course_id)
        course.status = 'approved'
        course.reviewed_by = request.user
        course.reviewed_at = timezone.now()
        course.save()

        # 🔥 Auto Announcement to Students
        create_auto_announcement(
            title=f"New Course Available: {course.name}",
            message=f"Dear Students,\n\nA new course **'{course.name}'** by {course.teacher.get_full_name() or course.teacher.username} has been approved and is now available for enrollment.",
            category='course',
            target_role='student',
            related_course=course
        )

        _log_activity(request.user, f'Approved course "{course.name}"')

        return JsonResponse({'status': 'ok', 'message': 'Course approved and students notified.'})
    except Course.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Course not found.'})


@admin_required
def admin_reject_course(request, course_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        import json
        data = json.loads(request.body)
        reason = data.get('reason', 'Not approved by admin')

        course = Course.objects.select_related('teacher').get(id=course_id)
        course.status = 'rejected'
        course.rejection_reason = reason
        course.reviewed_by = request.user
        course.reviewed_at = timezone.now()
        course.save()

        _log_activity(request.user, f'Rejected course "{course.name}"')

        return JsonResponse({'status': 'ok', 'message': 'Course rejected.'})
    except Course.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Course not found.'})


@admin_required
def admin_course_detail(request, course_id):
    """GET /eduexam-admin/course/<id>/detail/ — Quick View Panel"""

    # Accept both direct header and query param fallback
    if (request.headers.get('X-Requested-With') != 'XMLHttpRequest' and
            request.GET.get('ajax') != '1'):
        return JsonResponse({'status': 'error', 'message': 'AJAX only.'}, status=400)

    try:
        course = Course.objects.select_related(
            'teacher', 'teacher__profile'
        ).get(id=course_id)

        return JsonResponse({
            'status': 'ok',                    # ← MUST be "ok"
            'id': course.id,
            'name': course.name,
            'description': course.description or 'No description provided.',
            'teacher': course.teacher.get_full_name() or course.teacher.username,
            'teacher_email': course.teacher.email,
            'course_status': course.status,    # Renamed to avoid conflict
            'created_at': course.created_at.strftime('%d %b %Y, %I:%M %p'),
            'total_videos': getattr(course, 'total_videos', 0),
            'rejection_reason': getattr(course, 'rejection_reason', ''),
        })
    except Course.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Course not found.'})
    except Exception as e:
        print(f"[Course Detail Error] {e}")
        return JsonResponse({'status': 'error', 'message': 'Server error loading details.'}, status=500)

@admin_required
def admin_delete_course(request, course_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request.'})
    try:
        course = Course.objects.get(id=course_id)
        name = course.name
        course.delete()
        _log_activity(request.user, f'Deleted course "{name}"')
        return JsonResponse({'status': 'ok', 'message': f'Course "{name}" deleted successfully.'})
    except Course.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Course not found.'})


def create_auto_announcement(title, message, category, target_role='all', related_course=None, related_exam=None):
    try:
        ann = AdminAnnouncement.objects.create(
            title=title,
            message=message,
            category=category,
            target_role=target_role,
            priority='medium',
            created_by=None,
            related_course=related_course,
            related_exam=related_exam,
        )
        send_admin_announcement_email(ann)
        return ann
    except Exception as e:
        print(f"Auto announcement error: {e}")
        return None


# ====================== ADMIN ANNOUNCEMENTS ======================
@login_required(login_url='/auth/admin')
@admin_required
def admin_announcements(request):
    announcements = AdminAnnouncement.objects.all().order_by('-created_at')

    context = {
        'active_page': 'announcements',
        'announcements': announcements,
        'total_ann': announcements.count(),
        'pinned_count': announcements.filter(is_pinned=True).count(),
        **get_user_context(request.user),
    }
    return render(request, 'core/admin/admin_announcements.html', context)


@admin_required
def admin_create_announcement(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            message = request.POST.get('message')
            category = request.POST.get('category')
            target_role = request.POST.get('target_role')
            priority = request.POST.get('priority', 'medium')
            expires_at = request.POST.get('expires_at')

            ann = AdminAnnouncement.objects.create(
                title=title,
                message=message,
                category=category,
                target_role=target_role,
                priority=priority,
                created_by=request.user,
                is_pinned=request.POST.get('is_pinned') == 'on',
            )

            if expires_at:
                ann.expires_at = parse_datetime(expires_at)

            ann.save()

            # Send emails
            send_admin_announcement_email(ann)

            return JsonResponse({'status': 'ok', 'message': 'Announcement created and sent successfully!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def send_admin_announcement_email(ann):
    try:
        if ann.target_role == 'student':
            users = User.objects.filter(
                profile__role='student', is_active=True, profile__is_verified=True)
        elif ann.target_role == 'teacher':
            users = User.objects.filter(
                profile__role='teacher', is_active=True)
        else:
            users = User.objects.filter(
                is_active=True).exclude(profile__role='admin')

        subject = f"[{ann.get_category_display()}] {ann.title}"
        html_message = f"""
        <h2>{ann.title}</h2>
        <p>{ann.message}</p>
        <p><small>EduExam Admin • {ann.created_at.strftime('%d %b %Y')}</small></p>
        """

        for user in users[:100]:   # Limit to prevent spam
            send_mail(
                subject=subject,
                message=ann.message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,
            )
    except Exception as e:
        print(f"Announcement email error: {e}")


@admin_required
def admin_delete_announcement(request, ann_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'})
    try:
        ann = AdminAnnouncement.objects.get(id=ann_id)
        ann.delete()
        return JsonResponse({'status': 'ok'})
    except:
        return JsonResponse({'status': 'error'})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login_register/student/')
def student_start_exam(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.prefetch_related("options")

    if request.method == "POST":

        score = 0
        correct = 0
        wrong = 0
        unanswered = 0

        for question in questions:

            selected_option_id = request.POST.get(f"question_{question.id}")

            if not selected_option_id:
                unanswered += 1
                continue

            correct_option = question.options.filter(is_correct=True).first()

            if correct_option and str(correct_option.id) == selected_option_id:
                score += 1
                correct += 1
            else:
                wrong += 1

        StudentExamAttempt.objects.create(
            student=request.user,
            exam=exam,
            score=score,
            total_questions=questions.count(),
            correct_answers=correct,
            wrong_answers=wrong,
            unanswered=unanswered,
            percentage=(score / questions.count()) * 100 if questions.count() else 0,
            status="Passed" if score >= exam.passing_marks else "Failed"
        )

        return redirect("student_dashboard")

    return render(request, "core/student/student_start_exam.html", {
        "exam": exam,
        "questions": questions,
    })



# from django.utils import timezone
# from datetime import datetime, timedelta

# @login_required(login_url='/login_register/student')
# def student_examinations(request):

#     now = timezone.localtime()

#     upcoming_exams = []
#     ongoing_exams = []
#     completed_exams = []

#     for exam in Exam.objects.all():

#         if not exam.scheduled_date or not exam.scheduled_time:
#             continue

#         start = timezone.make_aware(
#             datetime.combine(exam.scheduled_date, exam.scheduled_time)
#         )

#         end = start + timedelta(minutes=exam.duration_minutes)

#         if now < start:
#             upcoming_exams.append(exam)

#         elif start <= now <= end:
#             ongoing_exams.append(exam)

#         else:
#             completed_exams.append(exam)

#     context = {
#         "upcoming_exams": upcoming_exams,
#         "ongoing_exams": ongoing_exams,
#         "completed_exams": completed_exams,
#         "missed_exams": [],

#         "upcoming_count": len(upcoming_exams),
#         "ongoing_count": len(ongoing_exams),
#         "completed_count": len(completed_exams),
#         "missed_count": 0,
#     }

#     return render(
#         request,
#         "core/student/student_examinations.html",
#         context,
#     )

from core.models import StudentExamAttempt

def teacher_results(request):

    results = StudentExamAttempt.objects.select_related(
        "student",
        "exam"
    ).order_by("-submitted_at")

    return render(request, "core/teacher/teacher_results.html", {
        "results": results,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

@login_required(login_url='/login_register/student')
def exam_rules(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    return render(request, 'core/student/exam_rules.html', {
        'exam': exam
    })