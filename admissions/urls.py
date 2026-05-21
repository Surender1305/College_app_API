from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApplicationViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
