from django.shortcuts import get_object_or_404
from django.db.models import prefetch_related_objects
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
import json


from rest_framework.decorators import action
from rest_framework import generics, mixins, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from education.redis_client import r

from course.models import Course
from course.permissions import IsEnrolled
from .models import Assignment, AssignmentSubmission, Question, SubmissionAnswer
from .serializers import AssignmentSerializer, AnswerSubmissionSerializer, SubmissionInfoSerializer, SubmissionSerializer


def session_key(student_id, assignment_id):
    return f"exam_session:student_{student_id}:assignment_{assignment_id}"
def assignment_key(assignment_id):
    return f"assignment:{assignment_id}"
# assignment cache only expire if the instractor change it by signals
class CachedAssignmentMixins:
    def check_exists(self, assignment_id):
        key = assignment_key(assignment_id)
        return r.exists(key)

    def cache_assignment(self, assignment):
        key = assignment_key(assignment.id)
        if self.check_exists(assignment.id):
            return
        
        question_answer_list = {}
        for question in assignment.questions.all(): 
            if question.answer_type == Question.AnswerType.MCQ:
                question_answer_list[question.id] = [ans.id for ans in question.mcq_answers.all()]
            else:
                question_answer_list[question.id] = []
        serializer = AssignmentSerializer(assignment)
        r.hset(key, mapping={
            "assignment_id": assignment.id,
            "questions": json.dumps(question_answer_list),
            "serializer": json.dumps(serializer.data)
        })

    def get_cached_assignment(self,assignment_id):
        if not self.check_exists(assignment_id):
            return None
        return r.hgetall(assignment_key(assignment_id))
    def get_questions(self, assignment_id):
        if not self.check_exists(assignment_id):
            return None
        return r.hget(assignment_key(assignment_id), "questions")
    def get_serializer(self, assignment_id):
        if not self.check_exists(assignment_id):
            return None
        return r.hget(assignment_key(assignment_id), "serializer")
        

class SubmissionStartView(APIView, CachedAssignmentMixins):
    permission_classes = [IsAuthenticated, IsEnrolled]

    def post(self, request, assignment_id):
        submission_key = session_key(request.user.student_info.id, assignment_id)
        # 1 check assignment exist
        assignment = get_object_or_404(Assignment, id=assignment_id)
        content = assignment.content.first()
        if not content:
            return Response({"error": "No content found"}, status=400)
        # 2 check student is enrolled
        self.check_object_permissions(self.request, content.module.course)
        # 3 check assignment is valid
        if not assignment.is_valid():
            return Response({"error": "Assignment is not valid"}, status=400)

        
        with transaction.atomic():
            submission_list = AssignmentSubmission.objects.select_for_update().filter(assignment=assignment,
                                                            student=request.user.student_info)
            # 4 check if user has already in progress submission
            submission = submission_list.filter(status=AssignmentSubmission.Status.PENDING).first()
            if submission:
                # 5 check if this submission isnt expired
                expiration_time = submission.started_at + assignment.duration
                if expiration_time < timezone.now():
                    submission.status = AssignmentSubmission.Status.EXPIRED
                    submission.save(update_fields=['status'])
                    r.delete(submission_key)
                    submission = None
                else:
                    # if submission is not expired, check if it is in cache
                    # if not, create a new one with the remaining time
                    if not r.exists(submission_key):
                        remaining = int((expiration_time - timezone.now()).total_seconds()) + 60
                        r.hset(submission_key, mapping={
                            "submission_id": submission.id,
                            "assignment_id": assignment.id,
                        })
                        r.expire(submission_key, remaining)

            # 6 check if there is no active submission
            if not submission or submission.status == AssignmentSubmission.Status.EXPIRED:
                if assignment.max_attempts is not None:
                        # 7 check if user has reached max attempts
                    terminal_statuses = [
                        AssignmentSubmission.Status.SUBMITTED,
                        AssignmentSubmission.Status.EXPIRED,
                        AssignmentSubmission.Status.CANCELED,
                    ]
                    attempts_used = submission_list.filter(
                        status__in=terminal_statuses
                    ).count()
                    if attempts_used >= assignment.max_attempts:
                        return Response(
                            {"error": "Maximum attempts reached"}, status=400
                        )
                        
                submission = AssignmentSubmission.objects.create(assignment=assignment, student=self.request.user.student_info)
                expiration_time = submission.started_at + assignment.duration
                r.hset(submission_key, mapping={
                        "submission_id": submission.id,
                        "assignment_id": assignment.id,
                    })
                expire_seconds = int(
                        (assignment.duration + timedelta(minutes=1)).total_seconds()
                    )
                r.expire(submission_key, expire_seconds)

        serializer = self.get_serializer(assignment_id)
        if not serializer:
            prefetch_related_objects([assignment], 'questions', 'questions__mcq_answers')
            self.cache_assignment(assignment)
            serializer = self.get_serializer(assignment_id)

        assignment_data = json.loads(serializer)
        
        
        return Response({
            "submission_id": submission.id,
            "expires_at": expiration_time,
            "assignment": assignment_data
        })

class AnswerSubmissionView(APIView, CachedAssignmentMixins):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id, question_id):
        # get data
        serializer = AnswerSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission_key = session_key(request.user.student_info.id, assignment_id)
        # check if submission exists in cache and not expired
        submission_session = r.hgetall(submission_key)
        if not submission_session:
            return Response({"error": "Assignment session not found, please reload the exam"}, status=400)
        
        submission_id = submission_session.get("submission_id")
        # check if assigment is cashed 
        raw_questions = self.get_questions(assignment_id)
        if not raw_questions:
            return Response({"error": "Assignment cache missing. Please reload the exam."}, status=400)
        questions = json.loads(raw_questions)

        #check if question exists and belongs to this assignment
        if str(question_id) not in questions:
            return Response({"error": "Question not found"}, status=400)
        
        # check if answer belongs to this question
        chosen_mcq = serializer.validated_data.get("chosen_mcq")
        if chosen_mcq:
            question_answers = questions.get(str(question_id))
            if chosen_mcq.id not in question_answers:
                return Response({"error": "Invalid answer"}, status=400)
        # create or update answer
        SubmissionAnswer.objects.update_or_create(
            submission_id=submission_id,
            question_id=question_id,
            defaults={
                'text_answer': serializer.validated_data.get('text_answer'),
                'file_answer': serializer.validated_data.get('file_answer'),
                'chosen_mcq': chosen_mcq,
            }
        )
        return Response({"message": "Answer submitted successfully"})
    

class SubmissionFinishView(APIView):
    permission_classes = [IsAuthenticated, IsEnrolled]
    # backup. if session expire
    def post(self, request, assignment_id, submission_id):
        submission = get_object_or_404(AssignmentSubmission.objects
                                       .select_related('assignment', 'student')
                                       .prefetch_related('answers', 'answers__question',
                                                        'answers__question__mcq_answers',
                                                        'answers__chosen_mcq'),
                                       id=submission_id, student=request.user.student_info)
        content = submission.assignment.content.first()
        if not content:
            return Response({"error": "No content found"}, status=400)
        # 2 check student is enrolled
        self.check_object_permissions(self.request, content.module.course)
        # get submission
        
        
        if submission.status == AssignmentSubmission.Status.SUBMITTED:
            return Response(SubmissionInfoSerializer(submission).data)
        if submission.status == AssignmentSubmission.Status.CANCELED:
            return Response({"error": "This submission has been canceled."}, status=400)

        answers_to_update = []
        for answer in submission.answers.all():
            if answer.question.answer_type == Question.AnswerType.MCQ:
                if answer.chosen_mcq and answer.chosen_mcq.is_correct:
                    answer.gained_marks = answer.question.question_marks
                else:
                    answer.gained_marks = 0
            else:
                answer.gained_marks = 0

            answers_to_update.append(answer)

        SubmissionAnswer.objects.bulk_update(answers_to_update, ['gained_marks'])


        submission.status = AssignmentSubmission.Status.SUBMITTED
        submission.submitted_at = timezone.now()
        r.delete(session_key(request.user.student_info.id, assignment_id))
        submission.save(update_fields=['status', 'submitted_at'])
        serializer = SubmissionInfoSerializer(submission)
        return Response(serializer.data)
    

class SubmissionListRetrieveView(mixins.ListModelMixin,
                                 mixins.RetrieveModelMixin,
                                 viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # assignment = get_object_or_404(Assignment, id=self.kwargs.get("assignment_id"))
        queryset = AssignmentSubmission.objects.filter(student=self.request.user.student_info)
        assignment = self.kwargs.get("assignment_id") or None
        if assignment:
            queryset = queryset.filter(assignment=assignment)
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('answers', 'answers__question', 'answers__question__mcq_answers', 'answers__chosen_mcq')
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubmissionSerializer
        return SubmissionInfoSerializer
    
    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        submission_id = self.kwargs.get("submission_id")
        obj = get_object_or_404(queryset, id=submission_id)
        return obj
    
    @action(detail=False, methods=['get'])
    def submissions_status(self, request, assignment_id):
        # Order by descending started_at to get the most recent attempt
        last_submission = AssignmentSubmission.objects.filter(
            student=self.request.user.student_info,
            assignment_id=assignment_id
        ).order_by('-started_at').values('id', 'status').first()
        
        if not last_submission:
            return Response({"status": "NOT_STARTED"})
        
        # Return the status, and include the ID so the frontend can close it if needed
        return Response({
            "status": last_submission["status"],
            "submission_id": last_submission["id"]
        })