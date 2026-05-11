from django.db import models

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey('users.User', on_delete=models.CASCADE)
    target_role = models.CharField(max_length=10, choices=(('ALL', 'All'), ('FACULTY', 'Faculty'), ('STUDENT', 'Student')), default='ALL')

    def __str__(self):
        return self.title

class Resource(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='resources/')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='resources')
    uploaded_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PendingAction(models.Model):
    TYPES = (
        ('LEAVE', 'Leave Request'),
        ('WAIVER', 'Fee Waiver'),
        ('ADMISSION', 'New Admission'),
        ('OTHER', 'Other'),
    )
    title = models.CharField(max_length=100)
    description = models.TextField()
    action_type = models.CharField(max_length=20, choices=TYPES, default='OTHER')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='PENDING') # PENDING, APPROVED, REJECTED
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='pending_actions')

    def __str__(self):
        return f"{self.title} - {self.status}"
