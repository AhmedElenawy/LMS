from django.db.models import Count
from rest_framework import serializers
from django.apps import apps

from course.models import (Course, Module, Content, Text, Video, Image,
                            File, Category, Discount, Enrollment)
from authentication.models import Instructor, Student

from assignment.models import Assignment


class ManageCourseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    instructor = serializers.PrimaryKeyRelatedField(read_only=True) 
    slug = serializers.SlugField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'overview', 'features', 
            'prequirements', 'image', 'base_price', 'category',
            'instructor',
        ]
class ManageModuleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    order = serializers.IntegerField(required=False, allow_null=True)
    course = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Module
        fields = ['id','title', 'description', 'order', 'course']


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'discount', 'valid_from', 'valid_to', 'active']

class EnrolledStudentSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='student.id', read_only=True)
    first_name = serializers.CharField(source='student.user.first_name', read_only=True)
    last_name = serializers.CharField(source='student.user.last_name', read_only=True)
    email = serializers.EmailField(source='student.user.email', read_only=True)
    enrolled_at = serializers.DateTimeField(source='date', read_only=True)
    progress_precentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'student_id', 'first_name', 'last_name', 'email',
                  'enrolled_at', 'progress_precentage']


class EnrollStudentSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ManageAssignmentViewSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='assignment', read_only=True)
    content_id = serializers.SerializerMethodField()
    def get_content_id(self, obj):
        return obj.content.first().id
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'created',
                   'updated', 'type',
                   'valid_from', 'valid_to', 'max_grade', 'active', "duration",
                     "max_attempts", 'content_id']