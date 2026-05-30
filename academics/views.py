from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from .models import Department, Course, Subject, Timetable, Attendance, Result, FeeStructure, StudentPayment
from .serializers import (
    DepartmentSerializer, CourseSerializer, SubjectSerializer, TimetableSerializer,
    AttendanceSerializer, ResultSerializer, FeeStructureSerializer, StudentPaymentSerializer
)

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Only admins may create/update/delete subjects."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Only admins may create/update/delete timetable slots."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'auto_generate']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Timetable.objects.all()
        course_id = self.request.query_params.get('course_id')
        semester = self.request.query_params.get('semester')
        faculty_id = self.request.query_params.get('faculty_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if semester:
            queryset = queryset.filter(semester=semester)
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)
        return queryset

    @action(detail=False, methods=['post'], url_path='auto-generate')
    def auto_generate(self, request):
        from django.db import transaction
        from users.models import User
        from rest_framework.response import Response
        from rest_framework import status
        
        course_id = request.data.get('course_id')
        semester = request.data.get('semester')
        
        if not course_id or not semester:
            return Response({'error': 'course_id and semester are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Get all subjects for this course
        subjects = list(Subject.objects.filter(course=course))
        if not subjects:
            return Response({'error': 'No subjects registered for this course. Please add subjects first.'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get all faculty members
        faculty_members = list(User.objects.filter(role='FACULTY'))
        if not faculty_members:
            return Response({'error': 'No faculty members registered. Please add faculty first.'}, status=status.HTTP_400_BAD_REQUEST)
            
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        slots_config = [
            ('09:00:00', '10:00:00'),
            ('10:00:00', '11:00:00'),
            ('11:15:00', '12:15:00'),
            ('13:00:00', '14:00:00'),
            ('14:00:00', '15:00:00'),
        ]
        
        generated_slots = []
        subject_index = 0
        
        # We will use transaction.atomic to ensure database consistency
        with transaction.atomic():
            # Delete existing slots for this course and semester to avoid partial duplicates or conflicts with old schedules
            Timetable.objects.filter(course=course, semester=semester).delete()
            
            for day in days:
                for start_t, end_t in slots_config:
                    # Find a free faculty member for this slot
                    busy_faculty_ids = Timetable.objects.filter(
                        day=day, 
                        start_time=start_t
                    ).values_list('faculty_id', flat=True)
                    
                    free_faculty = [f for f in faculty_members if f.id not in busy_faculty_ids]
                    
                    if not free_faculty:
                        selected_faculty = faculty_members[subject_index % len(faculty_members)]
                    else:
                        selected_faculty = free_faculty[0]
                        
                    # Find a free room
                    occupied_rooms = Timetable.objects.filter(
                        day=day,
                        start_time=start_t
                    ).values_list('room_number', flat=True)
                    
                    room_number = None
                    for r_num in [f"Room {i}" for i in range(101, 115)]:
                        if r_num not in occupied_rooms:
                            room_number = r_num
                            break
                    if not room_number:
                        room_number = f"Room {101 + (subject_index % 5)}"
                        
                    # Select subject in round-robin
                    selected_subject = subjects[subject_index % len(subjects)]
                    
                    # Create the slot
                    slot = Timetable.objects.create(
                        course=course,
                        subject=selected_subject,
                        faculty=selected_faculty,
                        day=day,
                        semester=semester,
                        start_time=start_t,
                        end_time=end_t,
                        room_number=room_number
                    )
                    generated_slots.append(slot)
                    subject_index += 1
                    
        return Response({
            'success': True,
            'message': f'Successfully generated {len(generated_slots)} slots for {course.name} Sem {semester}!',
            'data': TimetableSerializer(generated_slots, many=True).data
        }, status=status.HTTP_201_CREATED)

class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        course_id = request.data.get('course')
        year = request.data.get('year')
        if course_id and year:
            instance = FeeStructure.objects.filter(course_id=course_id, year=year).first()
            if instance:
                serializer = self.get_serializer(instance, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

class StudentPaymentViewSet(viewsets.ModelViewSet):
    queryset = StudentPayment.objects.all()
    serializer_class = StudentPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

from rest_framework import views, status
from rest_framework.response import Response
from users.models import User
from users.serializers import UserSerializer
from .models import Attendance, Result
from django.utils import timezone

class FacultySubjectsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'FACULTY':
            return Response({'error': 'Only faculty can access this'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get unique subjects assigned to this faculty in the timetable
        from .models import Timetable
        subjects_ids = Timetable.objects.filter(faculty=request.user).values_list('subject', flat=True).distinct()
        subjects = Subject.objects.filter(id__in=subjects_ids)
        
        data = SubjectSerializer(subjects, many=True).data
        return Response(data)

class FacultyStudentListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'FACULTY':
            return Response({'error': 'Only faculty can access this'}, status=status.HTTP_403_FORBIDDEN)
        
        course_id = request.query_params.get('course_id')
        semester = request.query_params.get('semester')
        
        students = User.objects.filter(role='STUDENT')
        if course_id:
            students = students.filter(department__courses__id=course_id)
        if semester:
            # Map semester back to year for simple demo
            # Assuming semester 1,2 -> year 1; 3,4 -> year 2; 5,6 -> year 3; 7,8 -> year 4
            year = (int(semester) + 1) // 2
            students = students.filter(year=year)
            
        data = UserSerializer(students, many=True).data
        return Response(data)

class MarkAttendanceView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'FACULTY':
            return Response({'error': 'Only faculty can access this'}, status=status.HTTP_403_FORBIDDEN)
            
        subject_id = request.data.get('subject_id')
        date_str = request.data.get('date', timezone.now().date().isoformat())
        attendance_data = request.data.get('attendance', []) # List of dicts: {'student_id': x, 'status': 'P'/'A'/'L'}
        
        if not subject_id or not attendance_data:
            return Response({'error': 'subject_id and attendance data are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)
            
        created_count = 0
        updated_count = 0
        
        for record in attendance_data:
            student_id = record.get('student_id')
            status_val = record.get('status', 'P')
            is_present = (status_val == 'P')
            
            try:
                student = User.objects.get(id=student_id, role='STUDENT')
                obj, created = Attendance.objects.update_or_create(
                    student=student,
                    subject=subject,
                    date=date_str,
                    defaults={'is_present': is_present, 'recorded_by': request.user}
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except User.DoesNotExist:
                continue
                
        return Response({
            'message': 'Attendance marked successfully',
            'created': created_count,
            'updated': updated_count
        })

class FacultyStudentStatsView(views.APIView):
    """Returns attendance stats per student for all subjects taught by this faculty."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'FACULTY':
            return Response({'error': 'Only faculty can access this'}, status=status.HTTP_403_FORBIDDEN)

        from .models import Timetable

        # Get all subjects this faculty teaches
        subject_ids = Timetable.objects.filter(faculty=request.user).values_list('subject', flat=True).distinct()
        subjects = Subject.objects.filter(id__in=subject_ids)

        # Get all students
        students = User.objects.filter(role='STUDENT')

        result = []
        for student in students:
            total = Attendance.objects.filter(student=student, subject__in=subjects).count()
            present = Attendance.objects.filter(student=student, subject__in=subjects, is_present=True).count()
            att_pct = round((present / total * 100), 1) if total > 0 else None

            dept = student.department
            result.append({
                'id': student.id,
                'username': student.username,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'department': {'name': dept.name, 'code': dept.code} if dept else None,
                'year': student.year,
                'attendance_total': total,
                'attendance_present': present,
                'attendance_pct': att_pct,
                'is_at_risk': att_pct is not None and att_pct < 75,
            })

        return Response(result)


class UploadMarksView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'FACULTY':
            return Response({'error': 'Only faculty can access this'}, status=status.HTTP_403_FORBIDDEN)
            
        subject_id = request.data.get('subject_id')
        exam_type = request.data.get('exam_type', 'INTERNAL_1')
        total_marks = request.data.get('total_marks', 100)
        marks_data = request.data.get('marks', []) # List of dicts: {'student_id': x, 'marks_obtained': y}
        
        if not subject_id or not marks_data:
            return Response({'error': 'subject_id and marks data are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)
            
        created_count = 0
        updated_count = 0
        
        for record in marks_data:
            student_id = record.get('student_id')
            marks_obtained = record.get('marks_obtained', 0)
            
            try:
                student = User.objects.get(id=student_id, role='STUDENT')
                obj, created = Result.objects.update_or_create(
                    student=student,
                    subject=subject,
                    exam_type=exam_type,
                    defaults={
                        'marks_obtained': marks_obtained, 
                        'total_marks': total_marks,
                        'recorded_by': request.user
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except User.DoesNotExist:
                continue
                
        return Response({
            'message': 'Marks uploaded successfully',
            'created': created_count,
            'updated': updated_count
        })

class StudentAttendanceView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        attendance = Attendance.objects.filter(student=request.user).order_by('-date')
        return Response(AttendanceSerializer(attendance, many=True).data)

class StudentResultView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        results = Result.objects.filter(student=request.user).order_by('-date_recorded')
        return Response(ResultSerializer(results, many=True).data)

class StudentFeeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        fee_structure = None

        # Safely navigate optional department → courses chain
        if user.department:
            course = user.department.courses.first()
            if course:
                fee_structure = FeeStructure.objects.filter(
                    course=course, year=user.year
                ).first()

        payments = StudentPayment.objects.filter(student=user).order_by('-date_paid')

        data = {
            'fee_structure': FeeStructureSerializer(fee_structure).data if fee_structure else None,
            'payments': StudentPaymentSerializer(payments, many=True).data,
            'total_paid': sum(p.amount_paid for p in payments),
        }
        return Response(data)
