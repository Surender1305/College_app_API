import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from academics.models import Department, Course

def populate():
    # Clear existing
    Course.objects.all().delete()
    Department.objects.all().delete()

    # MCA
    mca_dept = Department.objects.create(name='MCA', code='MCA')
    Course.objects.create(name='MCA', department=mca_dept, duration_years=2)

    # IC (Integrated Course)
    ic_dept = Department.objects.create(name='IC', code='IC')
    for sub in ['English', 'Chemistry', 'Physics', 'Math']:
        Course.objects.create(name=sub, department=ic_dept, duration_years=4)

    # BCA
    bca_dept = Department.objects.create(name='BCA', code='BCA')
    Course.objects.create(name='BCA', department=bca_dept, duration_years=3)

    print("Populated departments and courses successfully.")

if __name__ == '__main__':
    populate()
