from rest_framework.permissions import BasePermission

from .models import Course, Module

class IsEnrolled(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Course):
            return obj.students.filter(user=request.user).exists()
        elif isinstance(obj, Module):
            return obj.course.students.filter(user=request.user).exists()
        
        return True