from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, CourseViewSet, SubjectViewSet, TimetableViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'timetable', TimetableViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
