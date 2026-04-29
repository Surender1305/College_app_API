from rest_framework import serializers
from .models import Announcement, Resource
from users.serializers import UserSerializer

class AnnouncementSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model = Announcement
        fields = '__all__'

class ResourceSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    class Meta:
        model = Resource
        fields = '__all__'
