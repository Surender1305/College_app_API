import os
import django
import random
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from academics.models import Department, Course, Subject, Attendance

def seed():
    print("Seeding updated data...")
    
    # Create Departments
    mca_dept, _ = Department.objects.get_or_create(code='MCA', defaults={'name': 'MCA'})
    bca_dept, _ = Department.objects.get_or_create(code='BCA', defaults={'name': 'BCA'})
    bed_dept, _ = Department.objects.get_or_create(code='BED', defaults={'name': 'Education'})
    ic_dept, _ = Department.objects.get_or_create(code='IC', defaults={'name': 'Intermediate Commerce'})
    
    # New requested departments
    ic_eng, _ = Department.objects.get_or_create(code='IC_ENG', defaults={'name': 'IC (English)'})
    ic_che, _ = Department.objects.get_or_create(code='IC_CHE', defaults={'name': 'IC (Chemistry)'})
    ic_phy, _ = Department.objects.get_or_create(code='IC_PHY', defaults={'name': 'IC (Physics)'})
    ic_mat, _ = Department.objects.get_or_create(code='IC_MAT', defaults={'name': 'IC (Mathematics)'})
    
    depts = [mca_dept, bca_dept, bed_dept, ic_dept, ic_eng, ic_che, ic_phy, ic_mat]

    # Create Courses
    mca_course, _ = Course.objects.get_or_create(name='MCA', department=mca_dept, duration_years=2)
    bca_course, _ = Course.objects.get_or_create(name='BCA', department=bca_dept, duration_years=3)
    bed_course, _ = Course.objects.get_or_create(name='B.Ed', department=bed_dept, duration_years=2)
    
    # Create Subjects
    sub1, _ = Subject.objects.get_or_create(code='CS101', defaults={'name': 'Data Structures', 'course': mca_course, 'credits': 4})
    
    # Create Faculty
    faculty_user, created = User.objects.get_or_create(
        username='faculty',
        defaults={'role': 'FACULTY', 'first_name': 'Rajesh', 'last_name': 'Kumar', 'is_active': True}
    )
    if created:
        faculty_user.set_password('faculty')
        faculty_user.save()

    # Create Students
    for i in range(1, 101):
        username = f'student{i}'
        dept = random.choice(depts)
        student, created = User.objects.get_or_create(
            username=username,
            defaults={'role': 'STUDENT', 'first_name': f'Student', 'last_name': str(i), 'is_active': True, 'department': dept}
        )
        if created:
            student.set_password('student')
            student.save()
        else:
            student.department = dept
            student.save()
            
        # Create Attendance for today
        Attendance.objects.get_or_create(
            student=student,
            subject=sub1,
            date=timezone.now().date(),
            defaults={'is_present': random.choice([True, True, True, False]), 'recorded_by': faculty_user}
        )

    # Create Admin if not exists
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={'role': 'ADMIN', 'first_name': 'System', 'last_name': 'Admin', 'is_active': True}
    )
    if created:
        admin_user.set_password('admin')
        admin_user.save()

    print(f"Seed complete. Created {User.objects.count()} users.")

if __name__ == '__main__':
    seed()
