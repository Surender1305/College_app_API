from rest_framework import viewsets, permissions, views
from django.utils import timezone
from rest_framework.response import Response
from .models import Announcement, Resource
from .serializers import AnnouncementSerializer, ResourceSerializer

class DashboardStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        role = getattr(user, 'role', 'STUDENT').upper()
        today = timezone.now().date()

        if role == 'ADMIN':
            from django.contrib.auth import get_user_model
            from academics.models import Attendance, Department
            User = get_user_model()

            total_students = User.objects.filter(role='STUDENT').count()
            new_students   = User.objects.filter(role='STUDENT', date_joined__month=timezone.now().month).count()

            total_faculty    = User.objects.filter(role='FACULTY').count()
            faculty_on_leave = User.objects.filter(role='FACULTY', is_active=False).count()

            # Attendance Stats
            total_attendance_records = Attendance.objects.filter(date=today).count()
            present_records          = Attendance.objects.filter(date=today, is_present=True).count()
            attendance_percent = int((present_records / total_attendance_records * 100)) if total_attendance_records > 0 else 0

            # ── Enrollment by Department ────────────────────────────────────────
            mca_count = User.objects.filter(role='STUDENT', department__code='MCA').count()
            bca_count = User.objects.filter(role='STUDENT', department__code='BCA').count()
            bed_count = User.objects.filter(role='STUDENT', department__code='BED').count()

            # IC: aggregate all sub-departments whose group == 'IC'
            ic_dept_ids = Department.objects.filter(group='IC').values_list('id', flat=True)
            ic_count    = User.objects.filter(role='STUDENT', department_id__in=ic_dept_ids).count()

            # Per-IC sub-department breakdown for the dashboard
            ic_eng_count = User.objects.filter(role='STUDENT', department__code='IC_ENG').count()
            ic_che_count = User.objects.filter(role='STUDENT', department__code='IC_CHE').count()
            ic_mat_count = User.objects.filter(role='STUDENT', department__code='IC_MAT').count()
            ic_phy_count = User.objects.filter(role='STUDENT', department__code='IC_PHY').count()

            # Pending Approvals
            from .models import PendingAction
            pending_approvals = PendingAction.objects.filter(status='PENDING').order_by('-created_at')[:5]
            pending_data = []
            for action in pending_approvals:
                pending_data.append({
                    'id':    action.id,
                    'title': action.title,
                    'sub':   f"{action.user.first_name or action.user.username} • {action.get_action_type_display()}",
                    'time':  action.created_at.strftime('%H:%M %p') if action.created_at.date() == today else action.created_at.strftime('%b %d'),
                })

            # Fee Stats
            from academics.models import FeeStructure, StudentPayment
            from django.db.models import Sum

            total_expected_fees = 0
            for student in User.objects.filter(role='STUDENT').select_related('department'):
                course = student.department.courses.first() if student.department else None
                if course:
                    fs = FeeStructure.objects.filter(course=course, year=student.year).first()
                    if fs:
                        total_expected_fees += fs.tuition_fee + fs.lab_fee + fs.other_fees

            total_collected_fees = StudentPayment.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            fee_percent          = int((total_collected_fees / total_expected_fees * 100)) if total_expected_fees > 0 else 0
            pending_fee_count    = User.objects.filter(role='STUDENT').count() - StudentPayment.objects.values('student').distinct().count()

            # Latest Announcements
            announcements     = Announcement.objects.filter(target_role__in=['ALL', 'FACULTY', 'STUDENT']).order_by('-created_at')[:5]
            announcement_data = AnnouncementSerializer(announcements, many=True).data

            return Response({
                'enrollment': {
                    'total':      total_students,
                    'new':        new_students,
                    'graduating': int(total_students * 0.15),
                    'mca':        mca_count,
                    'bca':        bca_count,
                    'bed':        bed_count,
                    'ic':         ic_count,
                    # IC sub-department breakdown
                    'ic_eng':     ic_eng_count,
                    'ic_che':     ic_che_count,
                    'ic_mat':     ic_mat_count,
                    'ic_phy':     ic_phy_count,
                },
                'staff': {
                    'total':    total_faculty,
                    'on_leave': faculty_on_leave,
                },
                'attendance': {
                    'today_percent': attendance_percent,
                    'trend': 'up' if attendance_percent > 85 else 'stable',
                },
                'fees': {
                    'collected_percent': fee_percent,
                    'pending_count':     pending_fee_count,
                },
                'pending_approvals': pending_data,
                'announcements':     announcement_data,
            })


        elif role == 'FACULTY':
            from academics.models import Timetable, Subject, Attendance
            from academics.serializers import TimetableSerializer
            
            day_map = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}
            today_str = day_map.get(today.weekday(), 'MON')
            
            today_slots = Timetable.objects.filter(faculty=user, day=today_str).order_by('start_time')
            schedule_data = TimetableSerializer(today_slots, many=True).data
            
            # Check attendance completion for each slot
            for slot_data in schedule_data:
                subject_id = slot_data.get('subject')
                if subject_id:
                    is_completed = Attendance.objects.filter(subject_id=subject_id, date=today).exists()
                    slot_data['attendance_completed'] = is_completed
                else:
                    slot_data['attendance_completed'] = False
            
            # Compute real stats
            total_timetable_slots = Timetable.objects.filter(faculty=user).count()
            direct_subjects = Subject.objects.filter(faculty=user).count()
            total_subjects = max(direct_subjects, Timetable.objects.filter(faculty=user).values('subject').distinct().count())
            
            # Attendance records this faculty recorded
            pending_attendance = Attendance.objects.filter(recorded_by=user, date=today).count()
            total_students_taught = Timetable.objects.filter(faculty=user).values('course').distinct().count()
            
            return Response({
                'user_info': {
                    'name': f"{user.first_name} {user.last_name}" if user.first_name else user.username,
                    'department': user.department.name if user.department else "General Faculty",
                    'role': 'HOD' if getattr(user, 'is_hod', False) else 'Faculty',
                },
                'stats': {
                    'classes_today': today_slots.count(),
                    'total_subjects': total_subjects,
                    'total_slots': total_timetable_slots,
                    'pending_assignments': 0,
                    'student_feedback': 0.0,
                    'syllabus_progress': 0,
                },
                'today_schedule': schedule_data
            })
        else: # STUDENT
            from academics.models import Attendance, Subject, Timetable, Result
            from academics.serializers import TimetableSerializer
            from django.db.models import Sum, Avg
            
            # Attendance Stats
            total_att = Attendance.objects.filter(student=user).count()
            present_att = Attendance.objects.filter(student=user, is_present=True).count()
            att_percent = int((present_att / total_att) * 100) if total_att > 0 else 100
            
            # Credits from subjects in their course
            total_credits = Subject.objects.filter(course__department=user.department).aggregate(Sum('credits'))['credits__sum'] or 0
            
            # Dynamic course name from student's department
            course_name = "Degree"
            if user.department:
                course_obj = user.department.courses.first() if user.department.courses.exists() else None
                if course_obj:
                    course_name = course_obj.name
                else:
                    course_name = user.department.name
            
            # Compute GPA from actual results (percentage-based, scaled to 10)
            results_avg = Result.objects.filter(student=user).aggregate(
                avg_pct=Avg('marks_obtained')
            )['avg_pct']
            gpa = round(float(results_avg) / 10.0, 1) if results_avg else 0.0
            
            # Today's Timetable
            day_map = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}
            today_str = day_map.get(today.weekday(), 'MON')
            
            # Find timetable for the student's department and year/semester
            current_semester = 2 * user.year - 1 
            
            today_slots = Timetable.objects.filter(
                course__department=user.department,
                day=today_str,
                semester=current_semester
            ).order_by('start_time')
            
            schedule_data = TimetableSerializer(today_slots, many=True).data

            # Latest Announcements for Student
            announcements = Announcement.objects.filter(target_role__in=['ALL', 'STUDENT']).order_by('-created_at')[:3]
            announcement_data = AnnouncementSerializer(announcements, many=True).data

            return Response({
                'user_info': {
                    'name': f"{user.first_name} {user.last_name}" if user.first_name else user.username,
                    'roll_number': user.username,
                    'department': user.department.name if user.department else "General",
                    'course': course_name,
                    'semester': f"Semester {current_semester}",
                },
                'stats': {
                    'attendance': att_percent,
                    'gpa': gpa,
                    'credits': total_credits,
                    'assignments_due': 0,
                },
                'today_schedule': schedule_data,
                'announcements': announcement_data
            })

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all().order_by('-created_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all().order_by('-uploaded_at')
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
