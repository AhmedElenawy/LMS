from rest_framework.permissions import BasePermission
 
 
class IsInstructor(BasePermission):
    
 
    def has_permission(self, request, view):
        return hasattr(request.user, 'instructor_info')
    
    # def has_object_permission(self, request, view, obj):
    #     instructor = request.user.instructor_info

    #     # 1. Course
    #     if isinstance(obj, Course):
    #         return obj.instructor == instructor
        
    #     # 2. Module, Enrollment, discount
    #     if hasattr(obj, 'course'):
    #         return obj.course.instructor == instructor
            
    #     # 3. Content
    #     if hasattr(obj, 'module'):
    #         return obj.module.course.instructor == instructor
    #     # 4. Assignment
    #     if isinstance(obj, Assignment):
    #         content = obj.content.first()
    #         return content.module.course.instructor == instructor if content else False
    #     # 4. Question, AssignmentSubmission
    #     if hasattr(obj, 'assignment'):
    #         content = obj.assignment.content.first()
    #         return content.module.course.instructor == instructor if content else False

    #     # 5. SubmissionAnswer
    #     if hasattr(obj, 'submission'):
    #         content = obj.submission.assignment.content.first()
    #         return content.module.course.instructor == instructor if content else False

    #     return False   
    
    # def has_object_permission(self, request, view, obj):
    #     if isinstance(obj, Course):
    #         course = obj
    #     elif isinstance(obj, Module):
    #         course = obj.course
    #     elif isinstance(obj, Content):
    #         course = obj.module.course
    #     else:
    #         return False

    #     instructor = request.user.instructor_info
    #     if course.instructor == instructor:
    #         return True
        
    #     try:
    #         admin =  Admin.objects.get(admin=instructor, course=course)
    #     except Admin.DoesNotExist:
    #         return False

    #     method = request.method.lower()
    #     if method == 'post':
    #         return admin.can_add
    #     elif method in ['put', 'patch']:
    #         return admin.can_edit
    #     elif method == 'delete':
    #         return admin.can_delete
    #     elif method in permissions.SAFE_METHODS:
    #         return admin.can_view

    #     return False
