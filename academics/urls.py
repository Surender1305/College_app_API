from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, CourseViewSet, SubjectViewSet, TimetableViewSet
from .views import FacultyStudentListView, MarkAttendanceView, UploadMarksView, StudentAttendanceView, StudentResultView

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'timetable', TimetableViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('faculty/students/', FacultyStudentListView.as_view(), name='faculty-students'),
    path('faculty/attendance/', MarkAttendanceView.as_view(), name='faculty-attendance'),
    path('faculty/marks/', UploadMarksView.as_view(), name='faculty-marks'),
    path('student/attendance/', StudentAttendanceView.as_view(), name='student-attendance'),
    path('student/marks/', StudentResultView.as_view(), name='student-marks'),
]
