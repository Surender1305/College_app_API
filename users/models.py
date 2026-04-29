from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('FACULTY', 'Faculty'),
        ('STUDENT', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True)
    year = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Settings preferences
    biometric_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    reminders_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Profile of {self.user.username}"
