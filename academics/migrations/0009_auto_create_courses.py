"""
Data migration — automatically creates a default Course for any Department
that does not have one, ensuring fee structure and subject allocation can work.
"""
from django.db import migrations


def create_missing_courses(apps, schema_editor):
    Department = apps.get_model('academics', 'Department')
    Course = apps.get_model('academics', 'Course')

    for dept in Department.objects.all():
        if not dept.courses.exists():
            duration = 2 if dept.group == 'IC' or 'IC' in dept.code else 3
            # If code is BED, duration is 2
            if dept.code == 'BED':
                duration = 2
            elif dept.code == 'MCA':
                duration = 2
            
            Course.objects.create(
                name=dept.name,
                department=dept,
                duration_years=duration
            )


def reverse_migration(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0008_set_department_groups'),
    ]

    operations = [
        migrations.RunPython(create_missing_courses, reverse_migration),
    ]
