from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'management'

router = DefaultRouter()
router.register(r'courses', views.ManageCourseView, basename='course')

urlpatterns = [
    path('', include(router.urls)),

    # Modules — nested under course for full context
    path('courses/<int:course_pk>/modules/',
         views.ManageModuleView.as_view({'post': 'create'}),
         name='module-create'),
    path('courses/<int:course_pk>/modules/<int:pk>/',
         views.ManageModuleView.as_view({
             'get': 'retrieve',
             'put': 'update',
             'patch': 'partial_update',
             'delete': 'destroy',
         }),
         name='module-detail'),

    # Content — nested under module
    path('modules/<int:module_pk>/content/<str:model_name>/',
         views.ContentCreateView.as_view(),
         name='content-create'),
    path('modules/<int:module_pk>/content/item/<int:content_pk>/',
         views.ContentDeleteUpdateView.as_view(),
         name='content-detail'),

    # Questions — nested under assignment
    path('assignments/<int:assignment_pk>/questions/',
         views.ManageQuestionView.as_view({'get': 'list', 'post': 'create'}),
         name='assignment-questions-list'),
    path('assignments/<int:assignment_pk>/questions/<int:pk>/',
         views.ManageQuestionView.as_view({
             'get': 'retrieve',
             'put': 'update',
             'patch': 'partial_update',
             'delete': 'destroy',
         }),
         name='assignment-questions-detail'),

    # Submissions — nested under assignment
    path('assignments/<int:assignment_pk>/submissions/',
         views.ManageSubmissionView.as_view({'get': 'list'}),
         name='submission-list'),
    path('assignments/<int:assignment_pk>/submissions/<int:pk>/',
         views.ManageSubmissionView.as_view({'get': 'retrieve', 'delete': 'destroy'}),
         name='submission-detail'),

    # Answer grading — full context in URL
    path('assignments/<int:assignment_pk>/submissions/<int:submission_pk>/answers/<int:answer_pk>/',
         views.ManageAnswerGradingView.as_view(),
         name='answer-grading'),

    # Discount — guarded against duplicate creation in the view
    path('courses/<int:course_id>/discount/',
         views.ManageDiscountView.as_view({
             'get': 'retrieve',
             'put': 'update',
             'patch': 'partial_update',
             'delete': 'destroy',
             'post': 'create',
         }),
         name='discount-detail'),

    # Enrolled students
    path('courses/<int:course_id>/students/',
         views.ManageEnrolledStudentView.as_view({'get': 'list'}),
         name='enrolled-students-list'),
    path('courses/<int:course_id>/students/enroll/',
         views.ManageEnrolledStudentView.as_view({'post': 'enroll'}),
         name='enrolled-students-enroll'),
    path('courses/<int:course_id>/students/<int:pk>/',
         views.ManageEnrolledStudentView.as_view({'delete': 'destroy'}),
         name='enrolled-students-remove'),
]