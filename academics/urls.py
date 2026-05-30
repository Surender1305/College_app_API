from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, CourseViewSet, SubjectViewSet, TimetableViewSet, FeeStructureViewSet, StudentPaymentViewSet
from .views import FacultySubjectsView, FacultyStudentListView, FacultyStudentStatsView, MarkAttendanceView, UploadMarksView, StudentAttendanceView, StudentResultView, StudentFeeView

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'timetable', TimetableViewSet)
router.register(r'fees', FeeStructureViewSet)
router.register(r'payments', StudentPaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('faculty/subjects/', FacultySubjectsView.as_view(), name='faculty-subjects'),
    path('faculty/students/', FacultyStudentListView.as_view(), name='faculty-students'),
    path('faculty/student-stats/', FacultyStudentStatsView.as_view(), name='faculty-student-stats'),
    path('faculty/attendance/', MarkAttendanceView.as_view(), name='faculty-attendance'),
    path('faculty/marks/', UploadMarksView.as_view(), name='faculty-marks'),
    path('student/attendance/', StudentAttendanceView.as_view(), name='student-attendance'),
    path('student/marks/', StudentResultView.as_view(), name='student-marks'),
    path('student/fees/', StudentFeeView.as_view(), name='student-fees'),
]
