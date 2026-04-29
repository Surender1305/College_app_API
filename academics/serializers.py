from rest_framework import serializers
from .models import Department, Course, Subject, Timetable
from users.serializers import UserSerializer

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    class Meta:
        model = Course
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    class Meta:
        model = Subject
        fields = '__all__'

class TimetableSerializer(serializers.ModelSerializer):
    subject_details = SubjectSerializer(source='subject', read_only=True)
    faculty_details = UserSerializer(source='faculty', read_only=True)
    
    class Meta:
        model = Timetable
        fields = ('id', 'course', 'subject', 'faculty', 'day', 'semester', 'start_time', 'end_time', 'room_number', 'subject_details', 'faculty_details')
