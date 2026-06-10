from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from .models import Department, Course, Subject, Timetable, Attendance, Result, FeeStructure, StudentPayment
from .serializers import (
    DepartmentSerializer, CourseSerializer, SubjectSerializer, TimetableSerializer,
    AttendanceSerializer, ResultSerializer, FeeStructureSerializer, StudentPaymentSerializer
)

class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for attendance records, filterable by subject and date."""
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Attendance.objects.all()
        subject = self.request.query_params.get('subject')
        date = self.request.query_params.get('date')
        student = self.request.query_params.get('student')
        if subject:
            qs = qs.filter(subject_id=subject)
        if date:
            qs = qs.filter(date=date)
        if student:
            qs = qs.filter(student_id=student)
        return qs

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

class IsAdminOrHOD(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            return True
        if request.user.role == 'FACULTY' and getattr(request.user, 'is_hod', False):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            return True
        if request.user.role == 'FACULTY' and getattr(request.user, 'is_hod', False):
            if hasattr(obj, 'course') and obj.course and obj.course.department == request.user.department:
                return True
            if hasattr(obj, 'department') and obj.department == request.user.department:
                return True
        return False

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Only admins and HODs may create/update/delete subjects."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrHOD()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'FACULTY' and getattr(user, 'is_hod', False):
            course = serializer.validated_data.get('course')
            if course and course.department != user.department:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("HODs can only create subjects for courses in their department.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == 'FACULTY' and getattr(user, 'is_hod', False):
            course = serializer.validated_data.get('course')
            if course and course.department != user.department:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("HODs can only update subjects for courses in their department.")
        serializer.save()

class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Only admins and HODs may create/update/delete timetable slots."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'auto_generate']:
            return [permissions.IsAuthenticated(), IsAdminOrHOD()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'FACULTY' and getattr(user, 'is_hod', False):
            course = serializer.validated_data.get('course')
            if course and course.department != user.department:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("HODs can only create timetable slots for courses in their department.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == 'FACULTY' and getattr(user, 'is_hod', False):
            course = serializer.validated_data.get('course')
            if course and course.department != user.department:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("HODs can only update timetable slots for courses in their department.")
        serializer.save()

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
            
        # HOD restriction check on auto_generate
        user = request.user
        if user.role == 'FACULTY' and getattr(user, 'is_hod', False):
            if course.department != user.department:
                return Response({'error': 'HODs can only auto-generate timetables for courses in their department.'}, status=status.HTTP_403_FORBIDDEN)
            
        # Get all subjects for this course and semester
        subjects = list(Subject.objects.filter(course=course, semester=semester))
        if not subjects:
            return Response({'error': f'No subjects registered for {course.name} Sem {semester}. Please add subjects first.'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get all faculty members
        faculty_members = list(User.objects.filter(role='FACULTY'))
        if not faculty_members:
            return Response({'error': 'No faculty members registered. Please add faculty first.'}, status=status.HTTP_400_BAD_REQUEST)
            
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
        slots_config = [
            ('09:00:00', '09:50:00'),  # Class 1
            ('09:50:00', '10:40:00'),  # Class 2
            # 10:40:00 - 11:00:00 is Break
            ('11:00:00', '11:50:00'),  # Class 3
            ('11:50:00', '12:40:00'),  # Class 4
            # 12:40:00 - 13:30:00 is Lunch Break
            ('13:30:00', '14:20:00'),  # Class 5
            ('14:20:00', '15:10:00'),  # Class 6
            # 15:10:00 - 15:20:00 is Short Break
            ('15:20:00', '16:10:00'),  # Class 7
        ]
        
        # Parse subjects into categories
        labs = []
        pets = []
        theories = []
        for s in subjects:
            name_lower = s.name.lower()
            code_lower = s.code.lower()
            if 'pet' in name_lower or 'physical education' in name_lower or 'sports' in name_lower or 'games' in name_lower or 'p.e.t' in name_lower:
                pets.append(s)
            elif 'lab' in name_lower or 'practical' in name_lower or 'workshop' in name_lower or 'project' in name_lower:
                labs.append(s)
            else:
                theories.append(s)

        # We will keep a map of weekly count per subject
        subject_weekly_counts = {s.id: 0 for s in subjects}
        
        # Grid to hold the generated schedule locally before saving
        grid = {day: [None] * 7 for day in days}
        
        # Helper to check if faculty is busy at a slot in database or in our current grid
        def is_faculty_busy(faculty, day, slot_idx, start_t):
            # Check DB (excluding slots of the current course/semester being overwritten)
            if Timetable.objects.filter(day=day, start_time=start_t, faculty=faculty).exclude(course=course, semester=semester).exists():
                return True
            # Check current grid
            slot_val = grid[day][slot_idx]
            if slot_val and slot_val['faculty'].id == faculty.id:
                return True
            return False

        # Helper to find a free room
        def find_free_room(day, slot_idx, start_t, subject_index):
            occupied_rooms = list(Timetable.objects.filter(day=day, start_time=start_t).exclude(course=course, semester=semester).values_list('room_number', flat=True))
            # Also check current grid
            slot_val = grid[day][slot_idx]
            if slot_val:
                occupied_rooms.append(slot_val['room_number'])
            
            for r_num in [f"Room {i}" for i in range(101, 125)]:
                if r_num not in occupied_rooms:
                    return r_num
            return f"Room {101 + (subject_index % 5)}"

        # Helper to select faculty for a subject
        def get_faculty_for_subject(subject):
            if subject.faculty:
                return subject.faculty
            # Fallback to any faculty
            return faculty_members[subject.id % len(faculty_members)]

        def get_consecutive_slot_blocks(k):
            blocks = []
            for start in range(4 - k + 1):
                blocks.append(list(range(start, start + k)))
            for start in range(4, 7 - k + 1):
                blocks.append(list(range(start, start + k)))
            return blocks

        # 1. Schedule Labs (consecutive K slots on a single day where K is the target_periods)
        for lab_sub in labs:
            lab_faculty = get_faculty_for_subject(lab_sub)
            target_periods = getattr(lab_sub, 'periods_per_week', 2)
            scheduled = False
            for k in sorted([target_periods, 2, 1], reverse=True):
                if scheduled or k > target_periods:
                    continue
                blocks = get_consecutive_slot_blocks(k)
                for day in days:
                    if subject_weekly_counts[lab_sub.id] >= target_periods:
                        scheduled = True
                        break
                    for block in blocks:
                        if all(grid[day][idx] is None for idx in block):
                            conflict = False
                            for idx in block:
                                t_start, _ = slots_config[idx]
                                if is_faculty_busy(lab_faculty, day, idx, t_start):
                                    conflict = True
                                    break
                            if not conflict:
                                for idx in block:
                                    t_start, t_end = slots_config[idx]
                                    r = find_free_room(day, idx, t_start, lab_sub.id + idx)
                                    grid[day][idx] = {
                                        'subject': lab_sub,
                                        'faculty': lab_faculty,
                                        'room_number': r,
                                        'start_time': t_start,
                                        'end_time': t_end
                                    }
                                subject_weekly_counts[lab_sub.id] += len(block)
                                if subject_weekly_counts[lab_sub.id] >= target_periods:
                                    scheduled = True
                                    break

        # 2. Schedule PET (up to periods_per_week per week)
        for pet_sub in pets:
            pet_faculty = get_faculty_for_subject(pet_sub)
            target_periods = getattr(pet_sub, 'periods_per_week', 2)
            for day in days:
                if subject_weekly_counts[pet_sub.id] >= target_periods:
                    break
                # Try slot 6 (last period) first, then others
                for slot_idx in [6, 5, 4, 3, 2, 1, 0]:
                    if subject_weekly_counts[pet_sub.id] >= target_periods:
                        break
                    if grid[day][slot_idx] is None:
                        t_start, t_end = slots_config[slot_idx]
                        if not is_faculty_busy(pet_faculty, day, slot_idx, t_start):
                            r = find_free_room(day, slot_idx, t_start, pet_sub.id)
                            grid[day][slot_idx] = {
                                'subject': pet_sub,
                                'faculty': pet_faculty,
                                'room_number': r,
                                'start_time': t_start,
                                'end_time': t_end
                            }
                            subject_weekly_counts[pet_sub.id] += 1
                            break

        # 3. Schedule Theories in remaining slots
        if theories:
            for day in days:
                for slot_idx in range(7):
                    if grid[day][slot_idx] is None:
                        t_start, t_end = slots_config[slot_idx]
                        
                        # Sort theories by weekly count to keep them balanced
                        theories.sort(key=lambda t: subject_weekly_counts[t.id])
                        
                        for theory_sub in theories:
                            target_periods = getattr(theory_sub, 'periods_per_week', 3)
                            if subject_weekly_counts[theory_sub.id] >= target_periods:
                                continue
                            
                            sub_faculty = get_faculty_for_subject(theory_sub)
                            if not is_faculty_busy(sub_faculty, day, slot_idx, t_start):
                                r = find_free_room(day, slot_idx, t_start, theory_sub.id)
                                grid[day][slot_idx] = {
                                    'subject': theory_sub,
                                    'faculty': sub_faculty,
                                    'room_number': r,
                                    'start_time': t_start,
                                    'end_time': t_end
                                }
                                subject_weekly_counts[theory_sub.id] += 1
                                break
                                
        # Save scheduled slots
        generated_slots = []
        with transaction.atomic():
            # Delete existing slots for this course and semester to avoid partial duplicates or conflicts with old schedules
            Timetable.objects.filter(course=course, semester=semester).delete()
            
            for day in days:
                for slot_idx in range(7):
                    slot_val = grid[day][slot_idx]
                    if slot_val:
                        slot = Timetable.objects.create(
                            course=course,
                            subject=slot_val['subject'],
                            faculty=slot_val['faculty'],
                            day=day,
                            semester=semester,
                            start_time=slot_val['start_time'],
                            end_time=slot_val['end_time'],
                            room_number=slot_val['room_number']
                        )
                        generated_slots.append(slot)
                        
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
        batch = request.data.get('batch', '').strip()
        if course_id and year:
            instance = FeeStructure.objects.filter(course_id=course_id, year=year, batch=batch).first()
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
        
        # Union: subjects from timetable + subjects directly assigned via Subject.faculty FK
        from .models import Timetable
        timetable_subject_ids = set(Timetable.objects.filter(faculty=request.user).values_list('subject', flat=True).distinct())
        direct_subject_ids = set(Subject.objects.filter(faculty=request.user).values_list('id', flat=True))
        all_ids = timetable_subject_ids | direct_subject_ids
        subjects = Subject.objects.filter(id__in=all_ids).select_related('course', 'course__department')
        
        # Return with course as raw ID alongside nested details
        data = []
        for sub in subjects:
            item = {
                'id': sub.id,
                'name': sub.name,
                'code': sub.code,
                'credits': sub.credits,
                'semester': sub.semester,
                'course': sub.course_id,  # Raw integer ID for client-side filtering
                'course_details': {
                    'id': sub.course.id,
                    'name': sub.course.name,
                    'department': {
                        'id': sub.course.department.id,
                        'name': sub.course.department.name,
                        'code': sub.course.department.code,
                    } if sub.course.department else None,
                    'duration_years': sub.course.duration_years,
                } if sub.course else None,
            }
            data.append(item)
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
                # First try matching exact batch if student has a batch
                if getattr(user, 'batch', ''):
                    fee_structure = FeeStructure.objects.filter(
                        course=course, year=user.year, batch=user.batch
                    ).first()
                # Fallback to no-batch (empty string) structure if not found or student batch is empty
                if not fee_structure:
                    fee_structure = FeeStructure.objects.filter(
                        course=course, year=user.year, batch=''
                    ).first()

        payments = StudentPayment.objects.filter(student=user).order_by('-date_paid')

        data = {
            'fee_structure': FeeStructureSerializer(fee_structure).data if fee_structure else None,
            'payments': StudentPaymentSerializer(payments, many=True).data,
            'total_paid': sum(p.amount_paid for p in payments),
        }
        return Response(data)

class DownloadReceiptView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        from django.http import FileResponse
        from io import BytesIO
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        try:
            payment = StudentPayment.objects.get(pk=pk)
        except StudentPayment.DoesNotExist:
            return Response({'error': 'Payment record not found'}, status=status.HTTP_404_NOT_FOUND)

        # Security check: student can only download their own receipt. Admin/Faculty can download any.
        if request.user.role == 'STUDENT' and payment.student != request.user:
            return Response({'error': 'Unauthorized access to this receipt'}, status=status.HTTP_403_FORBIDDEN)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0F1E36'),
            alignment=1,
            spaceAfter=10
        )
        
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#4B5563'),
            alignment=1
        )

        normal_style = styles['Normal']
        bold_style = ParagraphStyle('BoldStyle', parent=normal_style, fontName='Helvetica-Bold')

        story = []

        # College Header details
        story.append(Paragraph("<b>POPE JOHN PAUL II COLLEGE OF EDUCATION</b>", title_style))
        story.append(Paragraph("Affiliated to Pondicherry University | Accredited by NAAC", header_style))
        story.append(Paragraph("Reddiarpalayam, Puducherry - 605010", header_style))
        story.append(Spacer(1, 15))

        story.append(Paragraph("<b>OFFICIAL PAYMENT RECEIPT</b>", ParagraphStyle('ReceiptTitle', parent=styles['Heading2'], fontSize=13, leading=15, textColor=colors.HexColor('#1E3A8A'), alignment=1, spaceAfter=20)))

        student = payment.student
        dept_name = student.department.name if student.department else 'N/A'
        batch_name = getattr(student, 'batch', 'N/A')
        date_str = payment.date_paid.strftime("%d-%b-%Y %I:%M %p")

        details_data = [
            [Paragraph("<b>Student Name:</b>", normal_style), Paragraph(f"{student.first_name} {student.last_name}".strip(), normal_style),
             Paragraph("<b>Receipt No:</b>", normal_style), Paragraph(f"REC-{payment.id:06d}", normal_style)],
            [Paragraph("<b>Roll Number:</b>", normal_style), Paragraph(student.username, normal_style),
             Paragraph("<b>Transaction ID:</b>", normal_style), Paragraph(payment.transaction_id, normal_style)],
            [Paragraph("<b>Course/Dept:</b>", normal_style), Paragraph(dept_name, normal_style),
             Paragraph("<b>Payment Date:</b>", normal_style), Paragraph(date_str, normal_style)],
            [Paragraph("<b>Year & Batch:</b>", normal_style), Paragraph(f"Year {student.year} ({batch_name})", normal_style),
             Paragraph("<b>Status:</b>", normal_style), Paragraph(f"<font color='green'><b>{payment.status}</b></font>", normal_style)]
        ]

        t_details = Table(details_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
        t_details.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LINEBELOW', (0,-1), (-1,-1), 1, colors.HexColor('#E5E7EB')),
        ]))
        story.append(t_details)
        story.append(Spacer(1, 20))

        # Payment Particulars Table
        part_data = [
            [Paragraph("<b>Particulars</b>", bold_style), Paragraph("<b>Payment Method</b>", bold_style), Paragraph("<b>Amount (INR)</b>", bold_style)],
            [Paragraph("College Academic Fee installment", normal_style), Paragraph(payment.payment_method, normal_style), Paragraph(f"Rs. {payment.amount_paid:.2f}", normal_style)],
            [Paragraph("<b>Total Paid</b>", bold_style), Paragraph("", normal_style), Paragraph(f"<b>Rs. {payment.amount_paid:.2f}</b>", bold_style)]
        ]
        
        t_part = Table(part_data, colWidths=[3.8*inch, 1.7*inch, 1.5*inch])
        t_part.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
            ('ALIGN', (2,0), (2,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F9FAFB')),
        ]))
        story.append(t_part)
        story.append(Spacer(1, 40))

        sig_data = [
            ["", Paragraph("For <b>POPE JOHN PAUL II COLLEGE</b>", ParagraphStyle('ForPJP', parent=normal_style, alignment=2))],
            ["", Spacer(1, 30)],
            ["", Paragraph("________________________<br/><b>Authorized Signatory</b>", ParagraphStyle('Sign', parent=normal_style, alignment=2))]
        ]
        t_sig = Table(sig_data, colWidths=[4.0*inch, 3.0*inch])
        t_sig.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_sig)

        doc.build(story)

        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"receipt_{payment.transaction_id}.pdf")

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import StudentDocument
from .serializers import StudentDocumentSerializer

def get_encryption_key():
    salt = b"PJP_Vault_Salt_Key"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))

class DocumentVaultViewSet(viewsets.ModelViewSet):
    serializer_class = StudentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'STUDENT':
            return StudentDocument.objects.filter(student=self.request.user).order_by('-uploaded_at')
        return StudentDocument.objects.all().order_by('-uploaded_at')

    def perform_create(self, serializer):
        student = self.request.user
        if self.request.user.role != 'STUDENT':
            student_id = self.request.data.get('student')
            if student_id:
                from users.models import User
                student = User.objects.get(id=student_id)
        
        uploaded_file = self.request.FILES.get('file')
        if not uploaded_file:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("File field is required.")

        file_bytes = uploaded_file.read()
        
        key = get_encryption_key()
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(file_bytes)

        encrypted_file = ContentFile(encrypted_bytes, name=uploaded_file.name)
        serializer.save(student=student, file=encrypted_file, name=uploaded_file.name)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        doc = self.get_object()
        
        # Security check: Student can only download their own documents. Faculty/Admin can download any.
        if request.user.role == 'STUDENT' and doc.student != request.user:
            return Response({'error': 'Unauthorized access to this document'}, status=status.HTTP_403_FORBIDDEN)

        try:
            doc.file.seek(0)
            encrypted_bytes = doc.file.read()
        except Exception as e:
            return Response({'error': f'Failed to read file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            key = get_encryption_key()
            fernet = Fernet(key)
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
        except Exception as e:
            return Response({'error': f'Failed to decrypt file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = HttpResponse(decrypted_bytes, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{doc.name}"'
        return response

