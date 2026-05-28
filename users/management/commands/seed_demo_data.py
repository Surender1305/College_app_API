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

        # 1. Create Departments (Using defaults for non-unique attributes to prevent IntegrityErrors)
        cs_dept, _ = Department.objects.get_or_create(code='CS', defaults={'name': 'Computer Science', 'head': 'Dr. Alan Turing'})
        me_dept, _ = Department.objects.get_or_create(code='ME', defaults={'name': 'Mechanical Engineering', 'head': 'Dr. Nikola Tesla'})
        mca_dept, _ = Department.objects.get_or_create(code='MCA', defaults={'name': 'MCA', 'head': 'Dr. Amit Sharma'})
        bca_dept, _ = Department.objects.get_or_create(code='BCA', defaults={'name': 'BCA', 'head': 'Dr. Priya Nair'})
        ic_eng, _ = Department.objects.get_or_create(code='IC_ENG', defaults={'name': 'IC (English)', 'head': 'Prof. John Keats'})
        ic_che, _ = Department.objects.get_or_create(code='IC_CHE', defaults={'name': 'IC (Chemistry)', 'head': 'Prof. Marie Curie'})
        ic_phy, _ = Department.objects.get_or_create(code='IC_PHY', defaults={'name': 'IC (Physics)', 'head': 'Prof. Albert Einstein'})
        ic_mat, _ = Department.objects.get_or_create(code='IC_MAT', defaults={'name': 'IC (Mathematics)', 'head': 'Prof. Isaac Newton'})

        # 2. Create Courses
        btech_cs, _ = Course.objects.get_or_create(name='B.Tech Computer Science', defaults={'department': cs_dept, 'duration_years': 4})
        btech_me, _ = Course.objects.get_or_create(name='B.Tech Mechanical Engineering', defaults={'department': me_dept, 'duration_years': 4})

        # 3. Create Subjects (Using defaults for code unique constraints)
        dsa, _ = Subject.objects.get_or_create(code='CS101', defaults={'name': 'Data Structures & Algorithms', 'course': btech_cs, 'credits': 4})
        dbms, _ = Subject.objects.get_or_create(code='CS102', defaults={'name': 'Database Management Systems', 'course': btech_cs, 'credits': 4})
        thermo, _ = Subject.objects.get_or_create(code='ME101', defaults={'name': 'Thermodynamics', 'course': btech_me, 'credits': 3})

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
            if not Timetable.objects.filter(course=btech_cs, subject=dsa, faculty=faculty1).exists():
                Timetable.objects.create(
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
        if not Announcement.objects.filter(title='Welcome to PJP College').exists():
            Announcement.objects.create(
                title='Welcome to PJP College',
                content='We are excited to have you all here for the new semester!',
                author=User.objects.get(username='admin'),
                target_role='ALL'
            )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
