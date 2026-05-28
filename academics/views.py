from rest_framework import viewsets, permissions
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

class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [permissions.IsAuthenticated]

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
        # Find fee structure for student's course and year
        fee_structure = FeeStructure.objects.filter(course=user.department.courses.first(), year=user.year).first()
        payments = StudentPayment.objects.filter(student=user).order_by('-date_paid')
        
        data = {
            'fee_structure': FeeStructureSerializer(fee_structure).data if fee_structure else None,
            'payments': StudentPaymentSerializer(payments, many=True).data,
            'total_paid': sum(p.amount_paid for p in payments)
        }
        return Response(data)
