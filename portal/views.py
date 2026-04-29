from rest_framework import viewsets, permissions, views
from django.utils import timezone
from rest_framework.response import Response
from .models import Announcement, Resource
from .serializers import AnnouncementSerializer, ResourceSerializer

class DashboardStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        role = getattr(user, 'role', 'STUDENT') 
        today = timezone.now().date()

        if role == 'ADMIN':
            from django.contrib.auth import get_user_model
            from academics.models import Attendance
            User = get_user_model()
            
            total_students = User.objects.filter(role='STUDENT').count()
            new_students = User.objects.filter(role='STUDENT', date_joined__month=timezone.now().month).count()
            
            total_faculty = User.objects.filter(role='FACULTY').count()
            # Faculty on leave could be a field, for now we count users with is_active=False as 'off'
            faculty_on_leave = User.objects.filter(role='FACULTY', is_active=False).count()
            
            # Attendance Stats
            total_attendance_records = Attendance.objects.filter(date=today).count()
            present_records = Attendance.objects.filter(date=today, is_present=True).count()
            attendance_percent = int((present_records / total_attendance_records * 100)) if total_attendance_records > 0 else 0

            # Enrollment Stats by Department
            mca_count = User.objects.filter(role='STUDENT', department__code='MCA').count()
            bca_count = User.objects.filter(role='STUDENT', department__code='BCA').count()
            bed_count = User.objects.filter(role='STUDENT', department__code='BED').count()
            ic_count = User.objects.filter(role='STUDENT', department__code='IC').count()

            return Response({
                'enrollment': {
                    'total': total_students,
                    'new': new_students,
                    'graduating': int(total_students * 0.15),
                    'mca': mca_count,
                    'bca': bca_count,
                    'bed': bed_count,
                    'ic': ic_count,
                },
                'staff': {
                    'total': total_faculty,
                    'on_leave': faculty_on_leave,
                },
                'attendance': {
                    'today_percent': attendance_percent,
                    'trend': 'up' if attendance_percent > 85 else 'stable',
                },
                'fees': {
                    'collected_percent': 72,
                    'pending_count': int(total_students * 0.1),
                }
            })

        elif role == 'FACULTY':
            from academics.models import Timetable
            from academics.serializers import TimetableSerializer
            
            day_map = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}
            today_str = day_map.get(today.weekday(), 'MON')
            
            today_slots = Timetable.objects.filter(faculty=user, day=today_str).order_by('start_time')
            schedule_data = TimetableSerializer(today_slots, many=True).data
            
            return Response({
                'user_info': {
                    'name': f"{user.first_name} {user.last_name}" if user.first_name else user.username,
                    'department': user.department.name if user.department else "General Faculty",
                    'role': 'Senior Lecturer', # Default for now
                },
                'stats': {
                    'classes_today': today_slots.count(),
                    'syllabus_progress': 65, # Placeholder or calculate from some model
                    'pending_assignments': 8,
                    'student_feedback': 4.7,
                },
                'today_schedule': schedule_data
            })
        else: # STUDENT
            from academics.models import Attendance, Subject
            from django.db.models import Sum
            
            total_att = Attendance.objects.filter(student=user).count()
            present_att = Attendance.objects.filter(student=user, is_present=True).count()
            att_percent = int((present_att / total_att) * 100) if total_att > 0 else 100
            
            total_credits = Subject.objects.filter(course__department=user.department).aggregate(Sum('credits'))['credits__sum'] or 0
            
            return Response({
                'attendance': att_percent,
                'gpa': 3.8,
                'credits': total_credits,
                'assignments_due': 2,
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
