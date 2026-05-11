from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    head = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    duration_years = models.IntegerField(default=4)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    credits = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Timetable(models.Model):
    DAYS_OF_WEEK = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'FACULTY'})
    day = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    semester = models.IntegerField(default=1)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.subject.name} on {self.day} at {self.start_time}"

class Attendance(models.Model):
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False)
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='recorded_attendances')

    class Meta:
        unique_together = ('student', 'subject', 'date')

    def __str__(self):
        return f"{self.student.username} - {self.subject.name} - {self.date}"

class Result(models.Model):
    EXAM_TYPES = (
        ('INTERNAL_1', 'Internal Assessment 1'),
        ('INTERNAL_2', 'Internal Assessment 2'),
        ('SEMESTER', 'End Semester'),
        ('ASSIGNMENT', 'Assignment'),
    )
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='INTERNAL_1')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='recorded_results')
    date_recorded = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'exam_type')

    def __str__(self):
        return f"{self.student.username} - {self.subject.name} ({self.exam_type}): {self.marks_obtained}/{self.total_marks}"

class FeeStructure(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.IntegerField(default=1)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    lab_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ('course', 'year')

    def __str__(self):
        return f"{self.course.name} - Year {self.year}: {self.total_fee()}"

    def total_fee(self):
        return self.tuition_fee + self.lab_fee + self.other_fees

class StudentPayment(models.Model):
    student = models.ForeignKey('users.User', on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=50, default='ONLINE')
    status = models.CharField(max_length=20, default='SUCCESS')

    def __str__(self):
        return f"{self.student.username} paid {self.amount_paid} on {self.date_paid}"
