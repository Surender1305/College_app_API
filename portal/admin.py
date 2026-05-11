from django.contrib import admin
from .models import Announcement, Resource, PendingAction

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'target_role', 'created_at')
    list_filter = ('target_role', 'created_at')

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'uploaded_by', 'uploaded_at')
    list_filter = ('subject', 'uploaded_at')

@admin.register(PendingAction)
class PendingActionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'action_type', 'status', 'created_at')
    list_filter = ('status', 'action_type', 'created_at')
    actions = ['approve_actions', 'reject_actions']

    def approve_actions(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_actions.short_description = "Approve selected actions"

    def reject_actions(self, request, queryset):
        queryset.update(status='REJECTED')
    reject_actions.short_description = "Reject selected actions"
