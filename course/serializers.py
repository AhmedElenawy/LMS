
from attr import has
from django.db.models import Count
from rest_framework import serializers
from django.apps import apps

from .models import (Course, Module, Content, Text, Video, Image, File, Category, Enrollment)
from authentication.models import Instructor


class CourseListSerializer(serializers.ModelSerializer):
    student_count = serializers.IntegerField(read_only=True, allow_null=True, required=False)
    category_name = serializers.ReadOnlyField(source='category.title')
    instructor_name = serializers.SerializerMethodField()
    overview_preview = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    
    def get_price(self, obj):
        return obj.price
    def get_discount_percentage(self, obj):
        return obj.get_discount()

 
    def get_instructor_name(self, obj):
        return obj.instructor.user.get_full_name()
    
    def get_overview_preview(self, obj):
        if obj.overview and len(obj.overview) > 150:
            return obj.overview[:150] + '...'
        return obj.overview
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'overview_preview',
                    'created', 'updated', 'image',
                    'base_price', 'discount_percentage', 'price',
                     'category_name',
                    'instructor_name', 'student_count']




class InstructorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
 
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    class Meta:
        model = Instructor
        fields = ['id', 'full_name', 'bio', 'image']

class InstructorCourseDetailSerializer(InstructorSerializer):
    top_courses = serializers.SerializerMethodField()

    def get_top_courses(self, obj):
        top_courses_qs = (obj.instructor_courses.annotate(student_count=Count("students"))
                          .order_by('-student_count')[:5])
        return CourseListSerializer(top_courses_qs, many=True, context=self.context).data
    class Meta(InstructorSerializer.Meta):
        fields = InstructorSerializer.Meta.fields + ['top_courses']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']





class ItemPreviewSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    updated = serializers.DateTimeField(read_only=True)
    item_type = serializers.SerializerMethodField()


    def get_item_type(self, obj):
        return obj.__class__.__name__
    
class ItemRelatedSerializer(serializers.RelatedField):
    def to_representation(self, value):
        serializer = ItemPreviewSerializer(value)
        return serializer.data
    

class ContentSerializer(serializers.ModelSerializer):
    item = ItemRelatedSerializer(read_only=True)
    is_completed = serializers.SerializerMethodField()
    def get_is_completed(self, obj):
        completed_ids = self.context.get('completed_ids', set())
        if obj.id in completed_ids:
            return True
        return False
    class Meta:
        model = Content
        fields = ['id', 'item', 'is_completed']


class ModuleSerializer(serializers.ModelSerializer):
    # contents = ContentSerializer(many=True, read_only=True)
    order = serializers.IntegerField(required=False, allow_null=True)
    class Meta:
        model = Module
        fields = ['id', 'title', 'description',
                   'order']
class ModuleContentSerializer(ModuleSerializer):
    contents = ContentSerializer(many=True, read_only=True)
    class Meta(ModuleSerializer.Meta):
        fields = ModuleSerializer.Meta.fields + ['contents']



class CourseDetailSerializer(serializers.ModelSerializer):
    is_enrolled = serializers.SerializerMethodField()
    student_count = serializers.IntegerField(read_only=True, allow_null=True, required=False)
    instructor = InstructorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    created = serializers.DateTimeField(read_only=True)
    updated = serializers.DateTimeField(read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    def get_price(self, obj):
        return obj.price
    def get_discount_percentage(self, obj):
        return obj.get_discount()
    def get_is_enrolled(self, obj):
        request = self.context['request']
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'student_info'):
                return obj.students.filter(user=request.user).exists()
        return False
        

    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'overview',
                  'features', 'prequirements', 'created',
                  'updated', 'image', 'base_price', 'discount_percentage', 'price',
                    'category',
                  'instructor', 'student_count', 'modules', 'is_enrolled']



class TextSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='text', read_only=True)
    class Meta:
        model = Text
        fields = ['id', 'title', 'description', 'body',
                   'created', 'updated', 'type']

class VideoSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='video', read_only=True)
    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'url',
                   'created', 'updated', 'type']

class ImageSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='image', read_only=True)
    class Meta:
        model = Image
        fields = ['id', 'title', 'description', 'image',
                   'created', 'updated', 'type']

class FileSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='file', read_only=True)
    class Meta:
        model = File
        fields = ['id', 'title', 'description', 'file',
                   'created', 'updated', 'type']
        

class ProgressSerializer(serializers.ModelSerializer):
    completed_items_ids = serializers.SerializerMethodField()
    def get_completed_items_ids(self, obj):
        return [item.id for item in obj.completed_items.all() if obj.completed_items.exists()]
    class Meta:
        model = Enrollment
        fields = ['id', 'progress_percentage', "date", "completed_items_ids"]
 