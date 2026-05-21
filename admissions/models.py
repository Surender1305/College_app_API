from django.db import models
from django.conf import settings
from academics.models import Department, Course

class Application(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    # Core
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='application')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    assigned_teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_applications', limit_choices_to={'role': 'FACULTY'})
    
    # Step 1: Personal Details
    full_name = models.CharField(max_length=255, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Step 2: Academic Details
    prev_school = models.CharField(max_length=255, blank=True)
    board = models.CharField(max_length=255, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    year_of_passing = models.IntegerField(null=True, blank=True)
    academic_subjects = models.TextField(blank=True)

    # Step 3: Course Selection
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_batch = models.CharField(max_length=50, blank=True)

    # Review Remarks
    teacher_remark = models.TextField(blank=True)
    admin_remark = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Application {self.id} - {self.student.username}"

class ApplicationDocument(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=50) # e.g., '10th', '12th', 'ID', 'Photo'
    file = models.FileField(upload_to='admissions/documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doc_type} for {self.application.id}"
