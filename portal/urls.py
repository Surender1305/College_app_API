from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnnouncementViewSet, ResourceViewSet, DashboardStatsView

router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet)
router.register(r'resources', ResourceViewSet)

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
