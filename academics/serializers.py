from rest_framework import serializers
from .models import Department, Course, Subject, Timetable, Result, FeeStructure, StudentPayment, StudentDocument
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
    class Meta:
        model = Subject
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.course:
            rep['course'] = CourseSerializer(instance.course).data
            rep['course_details'] = CourseSerializer(instance.course).data
        if instance.faculty:
            rep['faculty_details'] = UserSerializer(instance.faculty).data
        return rep

class TimetableSerializer(serializers.ModelSerializer):
    subject_details = SubjectSerializer(source='subject', read_only=True)
    faculty_details = UserSerializer(source='faculty', read_only=True)
    
    class Meta:
        model = Timetable
        fields = ('id', 'course', 'subject', 'faculty', 'day', 'semester', 'start_time', 'end_time', 'room_number', 'subject_details', 'faculty_details')

from .models import Attendance, Result

class AttendanceSerializer(serializers.ModelSerializer):
    student_details = UserSerializer(source='student', read_only=True)
    class Meta:
        model = Attendance
        fields = '__all__'

class ResultSerializer(serializers.ModelSerializer):
    student_details = UserSerializer(source='student', read_only=True)
    class Meta:
        model = Result
        fields = '__all__'

class FeeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = '__all__'

class StudentPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentPayment
        fields = '__all__'

class StudentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocument
        fields = ('id', 'student', 'document_type', 'name', 'uploaded_at')

