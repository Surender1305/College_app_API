from django.shortcuts import render
from rest_framework import generics, permissions, viewsets
from .models import User, Profile
from .serializers import UserSerializer, ProfileSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class ProfileSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    
    def get_permissions(self):
        # Allow any authenticated user to view profiles, but only admins to manage users
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'list']:
             return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role.upper())
        return queryset
