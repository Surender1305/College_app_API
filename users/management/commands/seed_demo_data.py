from django.core.management.base import BaseCommand
from users.models import User
from academics.models import Department, Course, Subject, Timetable
from portal.models import Announcement
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Seeds the database with demo data and credentials'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Create Departments
        cs_dept, _ = Department.objects.get_or_create(name='Computer Science', code='CS', head='Dr. Alan Turing')
        me_dept, _ = Department.objects.get_or_create(name='Mechanical Engineering', code='ME', head='Dr. Nikola Tesla')

        # 2. Create Courses
        btech_cs, _ = Course.objects.get_or_create(name='B.Tech Computer Science', department=cs_dept, duration_years=4)
        btech_me, _ = Course.objects.get_or_create(name='B.Tech Mechanical Engineering', department=me_dept, duration_years=4)

        # 3. Create Subjects
        dsa, _ = Subject.objects.get_or_create(name='Data Structures & Algorithms', code='CS101', course=btech_cs, credits=4)
        dbms, _ = Subject.objects.get_or_create(name='Database Management Systems', code='CS102', course=btech_cs, credits=4)
        thermo, _ = Subject.objects.get_or_create(name='Thermodynamics', code='ME101', course=btech_me, credits=3)

        # 4. Create Users
        # Admin
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@pjp.com', 'admin123')
            admin.role = 'ADMIN'
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created Admin: admin / admin123'))

        # Faculty
        if not User.objects.filter(username='faculty1').exists():
            faculty1 = User.objects.create_user('faculty1', 'faculty1@pjp.com', 'faculty123')
            faculty1.role = 'FACULTY'
            faculty1.department = cs_dept
            faculty1.save()
            self.stdout.write(self.style.SUCCESS('Created Faculty: faculty1 / faculty123'))
            
            # Add timetable for faculty
            Timetable.objects.get_or_create(
                course=btech_cs,
                subject=dsa,
                faculty=faculty1,
                day='MON',
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 30),
                room_number='Lab 1'
            )

        # Student
        if not User.objects.filter(username='student1').exists():
            student1 = User.objects.create_user('student1', 'student1@pjp.com', 'student123')
            student1.role = 'STUDENT'
            student1.department = cs_dept
            student1.save()
            self.stdout.write(self.style.SUCCESS('Created Student: student1 / student123'))

        # 5. Create Announcements
        Announcement.objects.get_or_create(
            title='Welcome to PJP College',
            content='We are excited to have you all here for the new semester!',
            author=User.objects.get(username='admin'),
            target_role='ALL'
        )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
