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
