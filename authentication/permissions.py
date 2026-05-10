from rest_framework.permissions import BasePermission


class IsProfileOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
    
class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'instructor_info')
    
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'student_info')