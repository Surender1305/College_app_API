from django.contrib import admin
from .models import Department, Course, Subject, Timetable, Attendance, Result, FeeStructure, StudentPayment

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'duration_years')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'course', 'credits')

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('subject', 'day', 'start_time', 'end_time', 'faculty', 'room_number')
    list_filter = ('day', 'course', 'semester')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'date', 'is_present')
    list_filter = ('date', 'subject', 'is_present')

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'exam_type', 'marks_obtained', 'total_marks')
    list_filter = ('exam_type', 'subject')

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('course', 'year', 'tuition_fee', 'lab_fee', 'other_fees')
    list_filter = ('course', 'year')

@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount_paid', 'date_paid', 'status')
    list_filter = ('status', 'date_paid')
