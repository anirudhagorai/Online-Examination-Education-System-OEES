from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.urls import reverse

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Profile
import random


# ------------------- Home -------------------
def home(request):
  return render(request,'core/home.html',{})

def login_register(request,role):
  return render(request,'core/login_register.html',{"role":role})


def auth_page(request, role):
  return render(request, 'core/login_register.html', {'role': role})


# ------------------- Student -------------------
def student_dashboard(request):
  context={
    'active_page': 'dashboard',
  }
  return render(request, 'core/student/student_dashboard.html', context)

def student_courses(request):
  context={
    'active_page':'courses',
  }
  return render(request, 'core/student/student_courses.html',context)


def student_examinations(request):
  context = {
    'active_page': 'examinations',
  }
  return render(request, 'core/student/student_examinations.html', context)


def student_results(request):
  context = {
    'active_page': 'results',
  }
  return render(request, 'core/student/student_results.html', context)


def student_profile(request):
  context = {
    'active_page': 'profile',
  }
  return render(request, 'core/student/student_profile.html', context)


def student_announcements(request):
  context = {
    'active_page': 'announcements',
  }
  return render(request, 'core/student/student_announcements.html', context)


# ------------------- Teacher -------------------

def teacher_dashboard(request):
  return render(request, 'core/teacher/teacher_dashboard.html', {'active_page':'dashboard'})



# ------------------- Login -------------------

def insert_login(request,role):
  if request.method == "POST":
    login_id=request.POST['lusername']
    password=request.POST['lpassword']

    user=authenticate(request,username=login_id,password=password)
    
    if user is not None:
      if user.profile.role!=role:
        messages.error(request, f"Invalid Role: You are registered as a {user.profile.role}")
        return redirect('auth_page',role=role)
      # check email verification
      if not user.profile.is_verified:
        messages.error(request, "Please verify your email first.")
        return redirect('verify_otp_page',username=user.username)
      
      login(request,user)
      
      if role == "student":
        return redirect("student_dashboard")
      if role == "teacher":
        return redirect("teacher_dashboard")
    
    else:
      messages.error(request,"Invalid username or password. Please try again")
      return redirect('auth_page',role=role)
  return redirect('home')


# ------------------- Register -------------------

def insert_register(request,role):
  if request.method == "POST":
    full_name = request.POST.get('rusername')
    email=request.POST.get('remail')
    password=request.POST.get('rpassword')
    confirm_password=request.POST.get('cpassword')
    dob=request.POST.get('dob')
    roll_number = request.POST.get('roll_number')
    teacher_id = request.POST.get('teacher_id')
    
    # 1. Decide which one is use unique username
    if role== "student":
      unique_id=roll_number
    else:
      unique_id=teacher_id
    # 2. Validation Checks
    if not unique_id:
      messages.error(request, f"Please provide your {role} ID.")
      return redirect('auth_page', role=role)
    if len(password)<8:
      messages.error(request, "Password must be at least 8 characters long.")
      return redirect('auth_page', role=role)
    
    if password != confirm_password:
      messages.error(request, "Password do not match.")
      return redirect('auth_page', role=role)
    
    if User.objects.filter(email=email).exists():
      messages.error(request, "This email is already registered. Please login or user a different email.")
      return redirect('auth_page', role=role)
    
    try:
      with transaction.atomic():
        if User.objects.filter(username=unique_id).exists():
          return JsonResponse({"status": "error","message": "Already Registered. Choose correct username"})

        # If all checks pass, create user
        user = User.objects.create_user(
          username=unique_id,
          email=email,
          password=password,
          first_name=full_name
        )
        user.is_active = False
        user.save()
        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Create profile
        Profile.objects.update_or_create(
          user=user,
          defaults={
            'role': role,
            'dob': dob,
            'roll_number': roll_number if role == "student" else None,
            'teacher_id': teacher_id if role == "teacher" else None,
            'otp': otp,
            'otp_created_at': timezone.now(),
            'is_verified': False
          }
          
        )

        # Send Email OTP
        send_mail(
          "Email Verification OTP",
          f"Your OTP is {otp}. It is valid for 2 minutes.",
          settings.EMAIL_HOST_USER,
          [email],
          fail_silently=False,
        )

      if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
          "status": "success",
          "redirect_url": reverse('verify_otp_page',kwargs={'username': unique_id})
        })
      return redirect('verify_otp_page', username=unique_id)
    
    except Exception as e:
      return JsonResponse({
        "status": "error",
        "message": str(e)
      })
      
  return redirect('auth_page',role=role)


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
      
      #Correct OTP
      if entered_otp == profile.otp:
        profile.is_verified = True
        profile.otp = None
        profile.otp_created_at = None
        profile.save()
        user.is_active = True
        user.save()
        
        return JsonResponse({
          "status": "success",
          "message": "Email verified successfully",
          "redirect_url": f"/auth/{profile.role}/"
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
  if request.method == "POST":
    username = request.POST.get("username")
    try:
      user = User.objects.get(username=username)
      profile = user.profile
      
      otp = str(random.randint(100000, 999999))
      
      profile.otp = otp
      profile.otp_created_at = timezone.now()
      profile.otp_attempts = 0
      profile.save()
      
      send_mail(
        "Email Verification OTP",
        f"Your OTP is {otp}. It is valid for 2 minutes.",
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
      )
      return JsonResponse({
        "status": "success",
        "message": "OTP resent successfully"
      })
    except User.DoesNotExist:
      return JsonResponse({
        "status": "error",
        "message": "User not found"
      })
  return redirect('home')
      
  
  
def verify_otp_page(request, username):
  return render(request, "core/verify_otp.html",{"username":username})