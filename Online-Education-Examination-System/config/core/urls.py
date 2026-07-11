from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
  path('',views.home,name='home'),
  path('login_register/<str:role>',views.login_register,name='login_register'),
  path('auth/admin/', views.admin_login, name='admin_login'),
  # Name parameters that redirect strings
  path('logout/', views.logout_user, name='logout'),

  # Admin

  # dashboard
  path('eduexam-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

  # user management
  path('eduexam-admin/teachers/',views.admin_teachers, name='admin_teachers'),
  path('eduexam-admin/teacher/<int:user_id>/detail/',views.admin_teacher_detail, name='admin_teacher_detail'),
  path('eduexam-admin/teacher/<int:user_id>/approve/',views.admin_approve_teacher, name='admin_approve_teacher'),
  path('eduexam-admin/teacher/<int:user_id>/reject/', views.admin_reject_teacher,  name='admin_reject_teacher'),
  path('eduexam-admin/teacher/<int:user_id>/revoke/', views.admin_revoke_teacher,  name='admin_revoke_teacher'),
  path('eduexam-admin/teacher/<int:user_id>/delete/', views.admin_delete_teacher,  name='admin_delete_teacher'),

  path('eduexam-admin/students/',
       views.admin_students,           name='admin_students'),
  path('eduexam-admin/students/export/',                views.admin_export_students,    name='admin_export_students'),
  path('eduexam-admin/student/<int:user_id>/detail/',   views.admin_student_detail,    name='admin_student_detail'),
  path('eduexam-admin/student/<int:user_id>/edit/',     views.admin_edit_student,      name='admin_edit_student'),
  path('eduexam-admin/student/<int:user_id>/toggle/',   views.admin_toggle_student,    name='admin_toggle_student'),
  path('eduexam-admin/toggle-student-login/', views.admin_toggle_student_login, name='admin_toggle_student_login'),
  path('eduexam-admin/student/<int:user_id>/suspend/',  views.admin_suspend_student,   name='admin_suspend_student'),
  path('eduexam-admin/student/<int:user_id>/unsuspend/',views.admin_unsuspend_student, name='admin_unsuspend_student'),
  path('eduexam-admin/student/<int:user_id>/enroll/',   views.admin_student_enroll,    name='admin_student_enroll'),
  path('eduexam-admin/student/<int:user_id>/unenroll/', views.admin_student_unenroll,  name='admin_student_unenroll'),
  path('eduexam-admin/student/<int:user_id>/delete/',   views.admin_delete_student,    name='admin_delete_student'),

  # course management
  path('eduexam-admin/courses/', views.admin_courses, name='admin_courses'),
  path('eduexam-admin/course/<int:course_id>/approve/',
views.admin_approve_course, name='admin_approve_course'),
  path('eduexam-admin/course/<int:course_id>/reject/',
views.admin_reject_course, name='admin_reject_course'),
  path('eduexam-admin/course/<int:course_id>/delete/',
views.admin_delete_course, name='admin_delete_course'),
  path('eduexam-admin/course/<int:course_id>/detail/',
views.admin_course_detail, name='admin_course_detail'),

  # Examination
  path('eduexam-admin/examinations/', views.admin_examinations, name='admin_examinations'),

  # results
  path('eduexam-admin/results/', views.admin_results, name='admin_results'),


  # analytics
  path('eduexam-admin/analytics/', views.admin_analytics, name='admin_analytics'),

  # profile
  path('eduexam-admin/profile/', views.admin_profile, name='admin_profile'),

  # reports
  path('eduexam-admin/reports/', views.admin_reports, name='admin_reports'),

  # messages
  path('eduexam-admin/messages/', views.admin_messages, name='admin_messages'),

  # Announcements
  path('eduexam-admin/announcements/',views.admin_announcements, name='admin_announcements'),
  path('eduexam-admin/announcements/create/',views.admin_create_announcement, name='admin_create_announcement'),
  path('eduexam-admin/announcements/<int:ann_id>/delete/',views.admin_delete_announcement, name='admin_delete_announcement'),

  # ── Admin Users list + bulk ───────────────────────────────────────
  path('eduexam-admin/users/', views.admin_users, name='admin_users'),
  path('eduexam-admin/users/export/',views.admin_users_export, name='admin_users_export'),
  path('eduexam-admin/users/bulk-delete/',views.admin_users_bulk_delete, name='admin_users_bulk_delete'),

    # ── Admin User single-record actions ─────────────────────────────
  path('eduexam-admin/user/<int:user_id>/detail/',views.admin_user_detail,  name='admin_user_detail'),
  path('eduexam-admin/user/<int:user_id>/edit/',views.admin_user_edit, name='admin_user_edit'),
  path('eduexam-admin/user/<int:user_id>/toggle/',views.admin_user_toggle, name='admin_user_toggle'),
  path('eduexam-admin/user/<int:user_id>/delete/',views.admin_user_delete, name='admin_user_delete'),

  path('auth/<str:role>/',views.auth_page,name='auth_page'),


  # Password Reset
  path('forgot-password/',views.forgot_password,name='forgot_password'),
  path('forgot-verify/<str:username>/',views.forgot_verify_otp, name='forgot_verify_otp'),
  path('ajax-forgot-verify/', views.ajax_verify_forgot_otp,name='ajax_verify_forgot_otp'),
  path('reset-password/<str:username>/', views.reset_password, name='reset_password'),



  #For Student Account
  path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

  path('student/courses/', views.student_courses, name='student_courses'),

  path('student/course/<int:course_id>/',
       views.course_player, name='course_player'),

  path('student/examinations/', views.student_examinations, name='student_examinations'),

  path('student/results/', views.student_results, name='student_results'),

  path('student/profile/', views.student_profile, name='student_profile'),

  path('student/announcements/', views.student_announcements, name='student_announcements'),
  path('student/announcement/send/',views.student_send_announcement, name='student_send_announcement'),
  path('student/announcement/<int:ann_id>/',views.student_view_announcement, name='student_view_announcement'),
  path('student/announcement/<int:ann_id>/delete/',views.student_delete_announcement, name='student_delete_announcement'),
  path('student/announcement/<int:ann_id>/edit/',views.handle_edit_message, name='student_edit_message'),

  path('student/announcements/recent/', views.student_recent_announcements, name='student_recent_announcements'),
  #For Teacher Account
  path('teacher/dashboard', views.teacher_dashboard, name='teacher_dashboard'),

  path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
  path('teacher/course/add/', views.teacher_add_course, name='teacher_add_course'),
  path('teacher/course/<int:course_id>/edit/', views.teacher_edit_course, name='teacher_edit_course'),
  path('teacher/course/<int:course_id>/delete/',views.teacher_delete_course, name='teacher_delete_course'),

  path('teacher/course/<int:course_id>/player/',
       views.teacher_course_player, name='teacher_course_player'),
  path('teacher/course/<int:course_id>/replace-video/',
       views.teacher_replace_video, name='teacher_replace_video'),


  path('teacher/examinations', views.teacher_examinations,name='teacher_examinations'),

  path('teacher/announcements/', views.teacher_announcements,name='teacher_announcements'),
  path('teacher/announcement/<int:ann_id>/',views.teacher_view_announcement, name='teacher_view_announcement'),
  path('teacher/announcement/create/',views.teacher_send_announcement, name='teacher_send_announcement'),
  path('teacher/announcement/<int:ann_id>/reply/',views.teacher_reply_message, name='teacher_reply_message'),
  path('teacher/announcement/<int:ann_id>/delete/',views.teacher_delete_announcement, name='teacher_delete_announcement'),
  path('teacher/announcement/<int:ann_id>/edit/',views.handle_edit_message, name='teacher_edit_message'),

  path('teacher/students', views.teacher_students,name='teacher_students'),
  path('teacher/results', views.teacher_results,name='teacher_results'),
  path('teacher/profile', views.teacher_profile, name='teacher_profile'),

  #Login & Register URLs
  path('insert_login/<str:role>/',views.insert_login,name='insert_login'),
  path('insert_register/<str:role>/',views.insert_register,name='insert_register'),

  #OTP verification page
  path('verify-otp/<str:username>/',views.verify_otp_page, name='verify_otp_page'),

  #AJAX OTP verification API
  path('ajax-verify-otp/',views.ajax_verify_otp,name='ajax_verify_otp'),

  #Resend OTP
  path("resend-otp/", views.resend_otp, name="resend_otp"),

  #Enrolment and Remove of enroll of Course
  path('student/enroll/<int:course_id>/',views.enroll_course,name='enroll_course'),
  path('student/unenroll/<int:course_id>/',views.unenroll_course, name='unenroll_course'),

  path('api/mark-messages-read/', views.mark_messages_read, name='mark_messages_read'),

  # -----------------------------progress---------------------------------
  path('student/course/<int:course_id>/update-progress/',
       views.update_course_progress, name='update_course_progress'),

  # ----------------------------update profile------------------------------
  path('update-profile/', views.update_profile, name='update_profile'),

  path('profile/send-email-otp/', views.send_email_change_otp,
       name='send_email_change_otp'),
  path('profile/verify-email-otp/', views.verify_email_change_otp,
       name='verify_email_change_otp'),

path('student/exam/<int:exam_id>/', views.student_start_exam, name='student_start_exam'),
path(
    'student/exam/<int:exam_id>/rules/',
    views.exam_rules,
    name='exam_rules'
),

]



