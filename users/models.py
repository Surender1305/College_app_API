from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('FACULTY', 'Faculty'),
        ('STUDENT', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    is_hod = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True)
    year = models.IntegerField(default=1)
    batch = models.CharField(max_length=15, blank=True, default='')

    def __str__(self):
        return f"{self.username} ({self.role})"

class Profile(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    # Personal info
    blood_group = models.CharField(max_length=5, blank=True, null=True, choices=BLOOD_GROUP_CHOICES)
    date_of_birth = models.DateField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)

    # Settings preferences
    biometric_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    reminders_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Profile of {self.user.username}"
