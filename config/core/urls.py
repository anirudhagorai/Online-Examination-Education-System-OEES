from django.urls import path
from . import views

urlpatterns = [
  path('',views.home,name='home'),
  path('login_register/<str:role>',views.login_register,name='login_register'),
  path('auth/<str:role>/',views.auth_page,name='auth_page'),
  
  #Name parameters that redirect strings
  
  #For Student Account
  path('student/dashboard', views.student_dashboard, name='student_dashboard'),
  path('student/courses', views.student_courses, name='student_courses'),
  path('student/examinations', views.student_examinations, name='student_examinations'),
  path('student/results', views.student_results, name='student_results'),
  path('student/profile', views.student_profile, name='student_profile'),
  path('student/announcements', views.student_announcements, name='student_announcements'),
  
  #For Teacher Account
  path('teacher/dashboard', views.teacher_dashboard, name='teacher_dashboard'), 
  
  #Login & Register URLs
  path('insert_login/<str:role>/',views.insert_login,name='insert_login'),
  path('insert_register/<str:role>/',views.insert_register,name='insert_register'),
  
  #OTP verification page
  path('verify-otp/<str:username>/',views.verify_otp_page, name='verify_otp_page'),
  
  #AJAX OTP verification API
  path('ajax-verify-otp/',views.ajax_verify_otp,name='ajax_verify_otp'),
  
  #Resend OTP
  path("resend-otp/", views.resend_otp, name="resend_otp"),
]
