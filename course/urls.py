from django.urls import path
from . import views

app_name = 'course'


urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:course_id>/modules/<int:module_id>/', views.ModuleContentView.as_view(), name='module_content_detail'),
    path('courses/<int:course_id>/modules/<int:module_id>/contents/<int:content_id>/', views.CourseContentView.as_view(), name='course_content_detail'),
    path('instructors/<int:pk>/courses/', views.InstructorCourseDetailView.as_view(), name='instructor_course_detail'),
    path('students/courses/', views.StudentEnrollmentCoursesView.as_view(), name='student_enrollment_courses'),
    path("contents/<int:content_id>/complete/", views.ContentCompleteView.as_view(), name="compelete_enroll"),
    path('courses/<int:course_id>/progress/', views.ProgressView.as_view())
]