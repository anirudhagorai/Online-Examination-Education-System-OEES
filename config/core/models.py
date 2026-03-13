from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    role=models.CharField(max_length=10,choices=ROLE_CHOICES)

    dob = models.DateField(null=True, blank=True)
    #student fields
    roll_number=models.CharField(max_length=20,blank=True,null=True,unique=True)

    #teacher fields
    teacher_id=models.CharField(max_length=20,blank=True,null=True,unique=True)
    
    #otp fields
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    otp_attempts = models.IntegerField(default=0)
    
    #otp Expiry Function
    def is_otp_expired(self):
        if self.otp_created_at:
            expiry_time = self.otp_created_at + timedelta(minutes=5)
            return timezone.now() > expiry_time
        return True

    def __str__(self):
        return self.user.username


