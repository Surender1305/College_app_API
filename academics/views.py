from rest_framework import viewsets, permissions
from .models import Department, Course, Subject, Timetable
from .serializers import DepartmentSerializer, CourseSerializer, SubjectSerializer, TimetableSerializer

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
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
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if semester:
            queryset = queryset.filter(semester=semester)
        return queryset
