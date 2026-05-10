from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Prefetch
from django.contrib.contenttypes.prefetch import GenericPrefetch
from django.contrib.auth.models import User

from rest_framework import generics, mixins, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from assignment.models import Assignment, AssignmentSubmission, SubmissionAnswer, Question
from assignment.serializers import (
    QuestionSerializer, SubmissionSerializer,
    SubmissionInfoSerializer, AnswerReviewSerializer,
)
from authentication.models import Student

from course.models import (Course, Module, Content, Text, Video, Image, File,
                           Discount, Enrollment)
from course.serializers import (CourseListSerializer, TextSerializer,
                                VideoSerializer, ImageSerializer,
                                FileSerializer, CourseDetailSerializer,
                                ModuleContentSerializer)
from .permissions import IsInstructor
from .serializers import (ManageCourseSerializer, ManageModuleSerializer,
                          DiscountSerializer, ManageAssignmentViewSerializer,
                          EnrolledStudentSerializer, EnrollStudentSerializer)



class ManageCourseView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ManageCourseSerializer
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def get_queryset(self):
        queryset = Course.objects.filter(instructor=self.request.user.instructor_info)
        if self.action == 'list':
            return queryset.select_related("category", "instructor__user", "discount")
        if self.action == 'retrieve':
            return queryset.select_related(
                "category", "instructor__user", "discount"
            ).prefetch_related('modules')
        return queryset

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user.instructor_info)



class ManageModuleView(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ModuleContentSerializer
        return ManageModuleSerializer

    def get_queryset(self):
        
        queryset = Module.objects.filter(
            course__instructor=self.request.user.instructor_info
        )
        if self.action == 'retrieve':
            content_querysets = [
                Text.objects.only('id', 'title', 'description', 'updated'),
                Video.objects.only('id', 'title', 'description', 'updated'),
                Image.objects.only('id', 'title', 'description', 'updated'),
                File.objects.only('id', 'title', 'description', 'updated'),
                Assignment.objects.all(),
            ]
            queryset = queryset.prefetch_related(
                Prefetch(
                    "contents",
                    queryset=Content.objects.prefetch_related(
                        GenericPrefetch('item', querysets=content_querysets)
                    ),
                )
            )
        return queryset

    def perform_create(self, serializer):
        
        course = get_object_or_404(
            Course,
            id=self.kwargs.get("course_pk"),
            instructor=self.request.user.instructor_info,
        )
        with transaction.atomic():
            serializer.save(course=course)



class ContentCreateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_serializer_class(self, model_name):
        serializers_map = {
            "text": TextSerializer,
            "video": VideoSerializer,
            "image": ImageSerializer,
            "file": FileSerializer,
            "assignment": ManageAssignmentViewSerializer,
        }
        return serializers_map.get(model_name.lower())

    def post(self, request, module_pk, model_name):
        
        module = get_object_or_404(
            Module,
            id=module_pk,
            course__instructor=request.user.instructor_info,
        )
        serializer_class = self.get_serializer_class(model_name)
        if not serializer_class:
            return Response({"error": "Invalid content type"}, status=400)

        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                item = serializer.save(creator=request.user)
                Content.objects.create(module=module, item=item)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ContentDeleteUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_serializer_class(self, model_name):
        serializers_map = {
            "text": TextSerializer,
            "video": VideoSerializer,
            "image": ImageSerializer,
            "file": FileSerializer,
            "assignment": ManageAssignmentViewSerializer,
        }
        return serializers_map.get(model_name.lower())

    def _get_content(self, module_pk, content_pk, instructor):
        
        return get_object_or_404(
            Content,
            id=content_pk,
            module_id=module_pk,
            module__course__instructor=instructor,
        )

    def get(self, request, module_pk, content_pk):
        content = self._get_content(module_pk, content_pk, request.user.instructor_info)
        item = content.item
        serializer_class = self.get_serializer_class(item.__class__.__name__)
        if not serializer_class:
            return Response({"error": "Invalid content type"}, status=400)
        return Response(serializer_class(item).data)

    def patch(self, request, module_pk, content_pk):
        content = self._get_content(module_pk, content_pk, request.user.instructor_info)
        item = content.item
        serializer_class = self.get_serializer_class(item.__class__.__name__)
        if not serializer_class:
            return Response({"error": "Invalid content type"}, status=400)

        serializer = serializer_class(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, module_pk, content_pk):
        content = self._get_content(module_pk, content_pk, request.user.instructor_info)
        content.item.delete()
        content.delete()
        return Response({"message": "Content deleted successfully"}, status=204)


class ManageQuestionView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = QuestionSerializer

    def _get_assignment(self):
        
        return get_object_or_404(
            Assignment,
            id=self.kwargs.get("assignment_pk"),
            content__module__course__instructor=self.request.user.instructor_info,
        )

    def get_queryset(self):
        return Question.objects.filter(
            assignment=self._get_assignment()
        ).prefetch_related("mcq_answers")

    def perform_create(self, serializer):
        serializer.save(assignment=self._get_assignment())



class ManageSubmissionView(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_serializer_class(self):
        if self.action == "list":
            return SubmissionInfoSerializer
        return SubmissionSerializer

    def _get_assignment(self):
        
        return get_object_or_404(
            Assignment,
            id=self.kwargs.get("assignment_pk"),
            content__module__course__instructor=self.request.user.instructor_info,
        )

    def get_queryset(self):
        return self._get_assignment().submissions.all()


class ManageAnswerGradingView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = AnswerReviewSerializer

    def get_queryset(self):
        return SubmissionAnswer.objects.all()

    def get_object(self):
        
        submission = get_object_or_404(
            AssignmentSubmission,
            id=self.kwargs.get("submission_pk"),
            assignment__content__module__course__instructor=self.request.user.instructor_info,
        )
        # Answer scoped to the already-validated submission — no further check needed.
        return get_object_or_404(
            SubmissionAnswer,
            id=self.kwargs.get("answer_pk"),
            submission=submission,
        )


class ManageDiscountView(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    # CHANGED: IsCourseInstructor → IsInstructor
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = DiscountSerializer
    queryset = Discount.objects.all()

    def get_object(self):
       
        course = get_object_or_404(
            Course.objects.filter(instructor=self.request.user.instructor_info)
                          .select_related("discount"),
            id=self.kwargs.get("course_id"),
        )
        if course.discount:
            return course.discount
        raise NotFound(detail="Discount not found")

    def perform_create(self, serializer):
        course = get_object_or_404(
            Course,
            id=self.kwargs.get("course_id"),
            instructor=self.request.user.instructor_info,
        )
        with transaction.atomic():
            serializer.save()
            course.discount = serializer.instance
            course.save()


class ManageEnrolledStudentView(mixins.ListModelMixin,
                                mixins.DestroyModelMixin,
                                viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_serializer_class(self):
        if self.action == 'enroll':
            return EnrollStudentSerializer
        return EnrolledStudentSerializer

    def _get_course(self):
        
        return get_object_or_404(
            Course.objects.filter(instructor=self.request.user.instructor_info),
            id=self.kwargs.get("course_id"),
        )

    def get_queryset(self):
        return Enrollment.objects.filter(
            course=self._get_course()
        ).select_related('student__user')

    @action(detail=False, methods=['post'])
    def enroll(self, request, course_id=None):
        course = self._get_course()
        serializer = EnrollStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email__iexact=email)
            student = user.student_info
        except (User.DoesNotExist, Student.DoesNotExist):
            return Response({'error': 'Student with this email not found'}, status=404)

        if Enrollment.objects.filter(student=student, course=course).exists():
            return Response({'error': 'Student is already enrolled'}, status=400)

        Enrollment.objects.create(student=student, course=course)
        return Response({'message': f'{email} enrolled successfully'}, status=201)