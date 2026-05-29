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

        # ── 1. Departments ─────────────────────────────────────────────────────
        # Use update_or_create so name/group are ALWAYS applied correctly,
        # even if the record already existed with stale values.

        mca_dept, _ = Department.objects.update_or_create(
            code='MCA',
            defaults={'name': 'MCA', 'head': 'Dr. Amit Sharma', 'group': None}
        )
        bca_dept, _ = Department.objects.update_or_create(
            code='BCA',
            defaults={'name': 'BCA', 'head': 'Dr. Priya Nair', 'group': None}
        )
        bed_dept, _ = Department.objects.update_or_create(
            code='BED',
            defaults={'name': 'B.Ed', 'head': 'Dr. Sunita Rao', 'group': None}
        )

        # IC sub-departments — grouped under "IC"
        ic_eng, _ = Department.objects.update_or_create(
            code='IC_ENG',
            defaults={'name': 'IC - English',     'head': 'Prof. John Keats',       'group': 'IC'}
        )
        ic_che, _ = Department.objects.update_or_create(
            code='IC_CHE',
            defaults={'name': 'IC - Chemistry',   'head': 'Prof. Marie Curie',      'group': 'IC'}
        )
        ic_mat, _ = Department.objects.update_or_create(
            code='IC_MAT',
            defaults={'name': 'IC - Mathematics', 'head': 'Prof. Isaac Newton',     'group': 'IC'}
        )
        ic_phy, _ = Department.objects.update_or_create(
            code='IC_PHY',
            defaults={'name': 'IC - Physics',     'head': 'Prof. Albert Einstein',  'group': 'IC'}
        )

        # Fix legacy stale IC / CS / ME departments if they exist
        Department.objects.filter(code='IC').update(name='IC - General', group='IC')
        Department.objects.filter(code__in=['CS', 'ME']).update(group=None)

        self.stdout.write(self.style.SUCCESS('Departments OK'))

        # ── 2. Courses ─────────────────────────────────────────────────────────
        mca_course, _ = Course.objects.get_or_create(
            name='MCA', defaults={'department': mca_dept, 'duration_years': 2}
        )
        bca_course, _ = Course.objects.get_or_create(
            name='BCA', defaults={'department': bca_dept, 'duration_years': 3}
        )
        bed_course, _ = Course.objects.get_or_create(
            name='B.Ed', defaults={'department': bed_dept, 'duration_years': 2}
        )

        # ── 3. Subjects ────────────────────────────────────────────────────────
        dsa,  _ = Subject.objects.get_or_create(code='CS101', defaults={'name': 'Data Structures & Algorithms', 'course': mca_course, 'credits': 4})
        dbms, _ = Subject.objects.get_or_create(code='CS102', defaults={'name': 'Database Management Systems',  'course': mca_course, 'credits': 4})

        # ── 4. Users ───────────────────────────────────────────────────────────
        # Admin
        admin, _ = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@pjp.com',
            'role': 'ADMIN',
            'is_superuser': True,
            'is_staff': True,
        })
        admin.set_password('admin123')
        admin.role = 'ADMIN'
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()
        self.stdout.write(self.style.SUCCESS('Admin: admin / admin123'))

        # Faculty
        faculty1, _ = User.objects.get_or_create(username='faculty1', defaults={
            'email': 'faculty1@pjp.com',
            'role': 'FACULTY',
            'department': mca_dept,
        })
        faculty1.set_password('faculty123')
        faculty1.role = 'FACULTY'
        faculty1.department = mca_dept
        faculty1.save()
        self.stdout.write(self.style.SUCCESS('Faculty: faculty1 / faculty123'))

        # Timetable for faculty1
        if not Timetable.objects.filter(course=mca_course, subject=dsa, faculty=faculty1).exists():
            Timetable.objects.create(
                course=mca_course, subject=dsa, faculty=faculty1,
                day='MON', semester=1,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 30),
                room_number='Lab 1',
            )

        # Student — one per IC sub-department so counts are non-zero
        demo_students = [
            ('student1', 'student1@pjp.com', mca_dept),
            ('student2', 'student2@pjp.com', bca_dept),
            ('student3', 'student3@pjp.com', bed_dept),
            ('student4', 'student4@pjp.com', ic_eng),
            ('student5', 'student5@pjp.com', ic_che),
            ('student6', 'student6@pjp.com', ic_mat),
            ('student7', 'student7@pjp.com', ic_phy),
        ]
        for uname, email, dept in demo_students:
            s, _ = User.objects.get_or_create(username=uname, defaults={
                'email': email, 'role': 'STUDENT', 'department': dept
            })
            s.set_password('student123')
            s.role = 'STUDENT'
            s.department = dept
            s.save()
        self.stdout.write(self.style.SUCCESS('Students: student1–7 / student123'))

        # ── 5. Announcements ───────────────────────────────────────────────────
        if not Announcement.objects.filter(title='Welcome to PJP College').exists():
            Announcement.objects.create(
                title='Welcome to PJP College',
                content='We are excited to have you all here for the new semester!',
                author=admin,
                target_role='ALL',
            )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

