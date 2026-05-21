from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Application, ApplicationDocument
from .serializers import ApplicationSerializer, ApplicationDocumentSerializer

def standardized_response(success, message, data=None):
    return {"success": success, "message": message, "data": data or {}}

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', '') == 'STUDENT':
            return Application.objects.filter(student=user)
        elif getattr(user, 'role', '') == 'FACULTY':
            return Application.objects.filter(assigned_teacher=user)
        elif getattr(user, 'role', '') == 'ADMIN':
            return Application.objects.all()
        return Application.objects.none()

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(detail=False, methods=['post'], url_path='save-draft')
    def save_draft(self, request):
        if getattr(request.user, 'role', '') != 'STUDENT':
            return Response(standardized_response(False, "Unauthorized"), status=403)
        
        application, created = Application.objects.get_or_create(student=request.user)
        serializer = self.get_serializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(status='DRAFT')
            return Response(standardized_response(True, "Draft saved successfully", serializer.data))
        return Response(standardized_response(False, "Validation error", serializer.errors), status=400)

    @action(detail=False, methods=['post'], url_path='submit')
    def submit_application(self, request):
        if getattr(request.user, 'role', '') != 'STUDENT':
            return Response(standardized_response(False, "Unauthorized"), status=403)
        
        try:
            application = Application.objects.get(student=request.user)
            if application.status != 'DRAFT':
                return Response(standardized_response(False, "Application already submitted"))
            
            serializer = self.get_serializer(application, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(status='SUBMITTED')
                return Response(standardized_response(True, "Application submitted successfully", serializer.data))
            return Response(standardized_response(False, "Validation error", serializer.errors), status=400)
        except Application.DoesNotExist:
            return Response(standardized_response(False, "No draft found to submit"), status=404)

    @action(detail=False, methods=['get'], url_path='status')
    def application_status(self, request):
        if getattr(request.user, 'role', '') != 'STUDENT':
            return Response(standardized_response(False, "Unauthorized"), status=403)
        
        try:
            application = Application.objects.get(student=request.user)
            return Response(standardized_response(True, "Status retrieved", self.get_serializer(application).data))
        except Application.DoesNotExist:
            return Response(standardized_response(False, "No application found"), status=404)

    # Admin Actions
    @action(detail=True, methods=['put'], url_path='approve')
    def approve_application(self, request, pk=None):
        if getattr(request.user, 'role', '') != 'ADMIN':
            return Response(standardized_response(False, "Unauthorized"), status=403)
        
        application = self.get_object()
        application.status = 'APPROVED'
        application.admin_remark = request.data.get('remark', '')
        application.save()
        return Response(standardized_response(True, "Application approved", self.get_serializer(application).data))

    @action(detail=True, methods=['put'], url_path='reject')
    def reject_application(self, request, pk=None):
        if getattr(request.user, 'role', '') != 'ADMIN':
            return Response(standardized_response(False, "Unauthorized"), status=403)
        
        application = self.get_object()
        application.status = 'REJECTED'
        application.admin_remark = request.data.get('remark', '')
        application.save()
        return Response(standardized_response(True, "Application rejected", self.get_serializer(application).data))

    @action(detail=True, methods=['post'], url_path='assign-teacher')
    def assign_teacher(self, request, pk=None):
        if getattr(request.user, 'role', '') != 'ADMIN':
            return Response(standardized_response(False, "Unauthorized"), status=403)
        
        application = self.get_object()
        teacher_id = request.data.get('teacher_id')
        if not teacher_id:
            return Response(standardized_response(False, "teacher_id required"), status=400)
        
        application.assigned_teacher_id = teacher_id
        application.status = 'UNDER_REVIEW'
        application.save()
        return Response(standardized_response(True, "Teacher assigned", self.get_serializer(application).data))

    # Teacher Actions
    @action(detail=True, methods=['post'], url_path='remark')
    def add_remark(self, request, pk=None):
        if getattr(request.user, 'role', '') != 'FACULTY':
            return Response(standardized_response(False, "Unauthorized"), status=403)
        
        application = self.get_object()
        if application.assigned_teacher != request.user:
            return Response(standardized_response(False, "Not assigned to you"), status=403)
        
        application.teacher_remark = request.data.get('remark', '')
        application.save()
        return Response(standardized_response(True, "Remark added", self.get_serializer(application).data))

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = ApplicationDocument.objects.all()
    serializer_class = ApplicationDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            application = Application.objects.get(student=request.user)
            request.data['application'] = application.id
            return super().create(request, *args, **kwargs)
        except Application.DoesNotExist:
            return Response(standardized_response(False, "No application found"), status=404)
