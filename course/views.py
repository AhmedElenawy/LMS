from django.shortcuts import get_object_or_404
from django.db.models import Count, Prefetch, prefetch_related_objects
from django.core.cache import cache
from django.contrib.contenttypes.prefetch import GenericPrefetch

from requests import get
from rest_framework.views import APIView
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from education.redis_client import r
from authentication.models import Instructor, Student
from assignment.models import Assignment

from .utilis.category_tree import build_tree
from .models import (Category, Course, Enrollment, Module, Content, Text,
                      Video, Image, File)
from .serializers import (CourseListSerializer, CourseDetailSerializer, TextSerializer,
                           VideoSerializer, ImageSerializer, FileSerializer,
                             ModuleSerializer, ModuleContentSerializer,
                               InstructorCourseDetailSerializer, ProgressSerializer)
from assignment.serializers import AssignmentInfoSerializer, SubmissionInfoSerializer
from .pagination import CoursePagination, SearchRelevancePagination
from .permissions import IsEnrolled
from .filters import CourseFilter
# Create your views here.


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        category_tree = cache.get('category_tree')
        if not category_tree:
            categories_qs = Category.objects.only("id", "title","slug", "lft", "level").order_by('tree_id', 'lft')
            category_tree = build_tree(categories_qs)
            cache.set('category_tree', category_tree)
        return Response(category_tree)
    

class CourseListView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]
    # pagination_class = CoursePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseFilter

    @property
    def pagination_class(self):
        if self.request.query_params.get('search'):
            return SearchRelevancePagination
        return CoursePagination

    def get_queryset(self):
        queryset = (Course.objects
                    .select_related("category", "instructor__user", "discount"))
        return queryset
    
class CourseDetailView(generics.RetrieveAPIView):
    queryset = (Course.objects
                .select_related("category", "instructor__user", "discount")
                .prefetch_related('modules'))
    serializer_class = CourseDetailSerializer



# class CourseModuleView(generics.RetrieveAPIView):
#     queryset = Module.objects.all()
#     serializer_class = ModuleSerializer

class ModuleContentView(APIView):
    permission_classes=[IsAuthenticated, IsEnrolled]

    def get(self, request, course_id, module_id):
        content_querysets = [
                Text.objects.only('id', 'title', 'description', 'updated'),
                Video.objects.only('id', 'title', 'description', 'updated'),
                Image.objects.only('id', 'title', 'description', 'updated'),
                File.objects.only('id', 'title', 'description', 'updated'),
            ]
        module = get_object_or_404(
            Module.objects.prefetch_related(
            Prefetch(
                "contents", 
                queryset=Content.objects.prefetch_related(
                    GenericPrefetch('item', querysets=content_querysets)
                )
            ),
            ),
            id=module_id,
            course_id=course_id,
        )
        self.check_object_permissions(self.request, module.course)

        completed_ids = set()
        if request.user.is_authenticated and hasattr(request.user, 'student_info'):
            enrollment = Enrollment.objects.filter(
                student=request.user.student_info, 
                course_id=course_id
            ).first()
            if enrollment:
                # Get a flat, fast list of IDs
                completed_ids = set(enrollment.completed_items.values_list('id', flat=True))

        # 2. Pass those IDs into the context
        context = {
            'request': request,
            'completed_ids': completed_ids
        }


        serializer = ModuleContentSerializer(module, context=context)
        return Response(serializer.data)

class InstructorCourseDetailView(generics.RetrieveAPIView):
    queryset = Instructor.related_objects.all().prefetch_related('instructor_courses__category')
    serializer_class = InstructorCourseDetailSerializer
    permission_classes = [AllowAny]


class StudentEnrollmentCoursesView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]
    pagination_class = CoursePagination

    def get_queryset(self):
        queryset = (Course.objects.filter(students__user=self.request.user)
                    .select_related("category", "instructor__user", "discount"))
        return queryset

class CourseContentView(APIView):
    permission_classes=[IsAuthenticated, IsEnrolled]

    def get(self, request, course_id, module_id, content_id):
        content_querysets = [
                Text.objects.only('id', 'title', 'description', 'updated'),
                Video.objects.only('id', 'title', 'description', 'updated'),
                Image.objects.only('id', 'title', 'description', 'updated'),
                File.objects.only('id', 'title', 'description', 'updated'),
                Assignment.objects.prefetch_related('submissions'),
            ]
        
        content = get_object_or_404(
            Content.objects.select_related("module__course").prefetch_related(
                GenericPrefetch('item', querysets=content_querysets)
            ),
            id=content_id,
            module_id=module_id,
            module__course_id=course_id,
        )
        # self.check_object_permissions(self.request, content.module.course)
        item = content.item
        course = content.module.course
        self.check_object_permissions(self.request, course)
        # item = self.get_object(course_id, module_id, content_id)

        if isinstance(item, Text):
            serializer = TextSerializer(item)
        elif isinstance(item, Video):
            serializer = VideoSerializer(item)
        elif isinstance(item, File):
            serializer = FileSerializer(item)
        elif isinstance(item, Image):
            serializer = ImageSerializer(item)
        elif isinstance(item, Assignment):
            serializer = AssignmentInfoSerializer(item)
        else:
            return Response({"error": "Unknown content type"}, status=400)
        
        return Response(serializer.data)

class ContentCompleteView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self, request, content_id):
        content = get_object_or_404(
            Content,
            id=content_id,
        )
        course = content.module.course
        enrollment = get_object_or_404(
            Enrollment, 
            student=request.user.student_info,
            course=course
        )

        enrollment.completed_items.add(content)
        total_content = Content.objects.filter(module__course=course).count()
        completed_content = enrollment.completed_items.count()
        if total_content > 0:
            enrollment.progress_percentage = (completed_content / total_content) * 100
        else:
            enrollment.progress_percentage = 0
        enrollment.save(update_fields=['progress_percentage'])
        return Response({"message": "Content completed successfully"}, status=200)
    
class ProgressView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, course_id):
        course = get_object_or_404(
            Course,
            id=course_id,
        )
        enrollment = get_object_or_404(
            Enrollment, 
            student=request.user.student_info,
            course=course
        )
        serializer = ProgressSerializer(enrollment)
        return Response(serializer.data)