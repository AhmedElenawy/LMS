from django.urls import path
from .views import (
    SubmissionStartView,
    AnswerSubmissionView,
    SubmissionFinishView,
    SubmissionListRetrieveView,
)
# Existing mappings
submission_list_retrieve = SubmissionListRetrieveView.as_view({
    'get': 'list',
})

submission_detail = SubmissionListRetrieveView.as_view({
    'get': 'retrieve',
})

submission_status_check = SubmissionListRetrieveView.as_view({
    'get': 'submissions_status', 
})

# --- NEW: Map retrieve for the nested assignment URL ---
submission_detail_by_assignment = SubmissionListRetrieveView.as_view({
    'get': 'retrieve',
})
urlpatterns = [
    path('assignments/<int:assignment_id>/start/', SubmissionStartView.as_view(), name='submission-start'),
    path('assignments/<int:assignment_id>/questions/<int:question_id>/answer/', AnswerSubmissionView.as_view(), name='answer-submission'),
    path('assignments/<int:assignment_id>/submissions/<int:submission_id>/finish/', SubmissionFinishView.as_view(), name='submission-finish'),
    path('submissions/', submission_list_retrieve, name='submission-list'),
    path('submissions/<int:submission_id>/', submission_detail, name='submission-detail'),
    
    path('assignments/<int:assignment_id>/submissions/status/', submission_status_check, name='submission-status-check'),
    path('assignments/<int:assignment_id>/submissions/<int:submission_id>/', submission_detail_by_assignment, name='assignment-submission-detail'),
]
