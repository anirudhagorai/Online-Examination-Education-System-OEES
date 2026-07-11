# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth.models import User
# from django.db.models import Count, Avg
# from django.utils.html import format_html
# from django.urls import reverse
# from django.utils import timezone

# from examinations.models import(
#   Subject, Course, StudentGroup,
#   QuestionBank, BankedQuestion, BankedChoice,
#   Examination, ExamQuestion, ExamChoice,
#   ExamEnrollment, ExamAttempt, StudentAnswer,
# )

# # SITE BRANDING

# admin.site.site_header = "EduExam Administration"
# admin.site.site_title = "EduExam Admin"
# admin.site.index_title = "Control Panel"

# # USER PROFILE INLINE

# class UserAdmin(BaseUserAdmin):
#   list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
#   list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
#   search_fields = ('username', 'email', 'first_name', 'last_name')
#   ordering = ('-date_joined',)
  
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)


# # Subject

# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#   list_display = ('name', 'code', 'exam_count', 'created_at')
#   search_fields = ('name', 'code')
#   ordering = ('name',)
  
#   def get_queryset(self, request):
#     return super().get_queryset(request).annotate(_exam_count=Count('examination', distinct=True))
  
#   def exam_count(self, obj):
#     return obj._exam_count
#   exam_count.short_description = 'Exams'
#   exam_count.admin_order_field = '_exam_count'
  
# # Course & Group

# class StudentGroupInline(admin.TabularInline):
#   model = StudentGroup
#   extra = 0
#   fields = ('name', 'student_count')
#   readonly_fields = ('student_count',)
  
#   def student_count(self, obj):
#     return obj.students.count()
#   student_count.short_description = 'Students'

# @admin.register(Course)
# class CourseAdmin(admin.ModelAdmin):
#   list_display = ('name', 'code', 'subject', 'teacher', 'group_count', 'created_at')
#   list_filter = ('subject', 'teacher')
#   search_fields = ('name', 'code', 'teacher__username')
#   raw_id_fields = ('teacher',)
#   inlines = [StudentGroupInline]
  
#   def get_queryset(self, request):
#     return super().get_queryset(request).annotate(_group_count=Count('groups', distinct=True))

#   def group_count(self, obj):
#     return obj._group_count
#   group_count.short_description = 'Groups'
  

# @admin.register(StudentGroup)
# class StudentGroupAdmin(admin.ModelAdmin):
#   list_display = ('name', 'course', 'student_count', 'created_at')
#   list_filter = ('course',)
#   search_fields = ('name', 'course__name')
#   filter_horizontal = ('students',)
  
#   def student_count(self, obj):
#     return obj.students.count()
#   student_count.short_description = 'Students'
  
# # Question Bank
  
# class BankedChoiceInline(admin.TabularInline):
#   model = BankChoice
#   extra = 2
#   fields = ('choice_text', 'is_correct', 'order')


# @admin.register(QuestionBank)
# class StudentGroupAdmin(admin.ModelAdmin):
#   list_display = ('name', 'subject', 'teacher', 'question_count', 'is_shared', 'created_at')
#   list_filter = ('is_shared', 'subject', 'teacher')
#   search_fields = ('name', 'teacher__username')
#   filter_horizontal = ('teacher',)
  
#   def question_count(self, obj):
#     return obj.banked_questions.count()
#   question_count.short_description = 'Questions'


# @admin.register(BankedQuestion)
# class BankedQuestionAdmin(admin.ModelAdmin):
#   list_display = ('short_text', 'bank', 'subject', 'chapter', 'usage_count')
#   list_filter = ('subject', 'bank')
#   search_fields = ('question_text', 'chapter', 'tags')
#   inlines = [BankedChoiceInline]
#   filter_horizontal = ('usage_count',)
  
#   def short_text(self, obj):
#     return obj.question_text[:60] + ('-' if len(obj.question_text) > 60 else '')
#   short_text.short_description = 'Question'


# # Examination

# class ExamChoiceInline(admin.TabularInline):
#   model = ExamChoice
#   extra = 2
#   fields = ('choice_text', 'is_correct', 'order')
  

# class ExamQuestionInline(admin.TabularInline):
#   model = ExamQuestion
#   extra = 0
#   fields = ('question_text', 'question_type', 'marks', 'order')
#   show_change_link = True


# @admin.register(QuestionBank)
# class ExamQuestionAdmin(admin.ModelAdmin):
#   list_display = ('short_text', 'examination',  'marks', 'order', 'section')
#   list_filter = ('question_type', 'difficulty', 'examination')
#   search_fields = ('question_text', 'examination__title')
#   inlines = [ExamChoiceInline]

#   def short_text(self, obj):
#     return obj.question_text[:60] + ('-' if len(obj.question_text) > 60 else '')
#   short_text.short_description = 'Question'
  

# @admin.register(Examination)
# class ExamQuestionAdmin(admin.ModelAdmin):
#   list_display = ('title', 'subject',  'marks', 'order', 'section')
#   list_filter = ('question_type', 'difficulty', 'examination')
#   search_fields = ('question_text', 'examination__title')
#   inlines = [ExamChoiceInline]

#   def short_text(self, obj):
#     return obj.question_text[:60] + ('-' if len(obj.question_text) > 60 else '')
#   short_text.short_description = 'Question'

