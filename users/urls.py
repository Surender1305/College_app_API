from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import UserProfileView, UserViewSet, ProfileSettingsView, ChangePasswordView, VerifyQRView

router = DefaultRouter()
router.register(r'manage', UserViewSet, basename='user-manage')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('settings/', ProfileSettingsView.as_view(), name='user_settings'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('verify-qr/', VerifyQRView.as_view(), name='verify_qr'),
    path('', include(router.urls)),
]

