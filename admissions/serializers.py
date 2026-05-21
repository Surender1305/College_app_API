from rest_framework import serializers
from .models import Application, ApplicationDocument
from users.serializers import UserSerializer
from academics.serializers import DepartmentSerializer, CourseSerializer

class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = '__all__'

class ApplicationSerializer(serializers.ModelSerializer):
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    student_details = UserSerializer(source='student', read_only=True)
    department_details = DepartmentSerializer(source='department', read_only=True)
    course_details = CourseSerializer(source='course', read_only=True)
    assigned_teacher_details = UserSerializer(source='assigned_teacher', read_only=True)

    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ('student', 'status', 'created_at', 'updated_at')
