from rest_framework import serializers

from django.contrib.auth.models import User
from .models import Instructor, Student
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import transaction
from django.contrib.auth.password_validation import validate_password

class ValidateEmailMixin:
    def validate_email(self, value):
        email = value.lower().strip()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return email
        
        if user and not user.is_active:
            user.delete()
            return email
        
        raise serializers.ValidationError('User with this email already exists.')

class StudentProfileSerializer(serializers.HyperlinkedModelSerializer):
    # Change from ReadOnlyField to CharField
    first_name = serializers.CharField(source='user.first_name', allow_null=True, required=False)
    last_name = serializers.CharField(source='user.last_name', allow_null=True, required=False)

    class Meta:
        model = Student
        fields = ('first_name', 'last_name', 'date_of_birth', 'title')
        
    def update(self, instance, validated_data):
        # 1. Extract and update the nested User data
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        instance.user.save()

        # 2. Update the Student profile data
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.title = validated_data.get('title', instance.title)
        instance.save()

        return instance
class StudentRegisterSerializer(serializers.HyperlinkedModelSerializer, ValidateEmailMixin):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True)
    profile = StudentProfileSerializer(source='student_info')
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'profile')

    
    def create(self, validated_data):
        password = validated_data.pop('password')
        profile_data = validated_data.pop('student_info')
        email = validated_data['email']
        username = validated_data.get('username') or email 
        with transaction.atomic():
            user = User(username=username,
                         email=validated_data['email'],
                           first_name=validated_data['first_name'],
                             last_name=validated_data['last_name'],
                             is_active=False)
            user.set_password(password)
            user.save()
            Student.objects.create(user=user, **profile_data)
        return user

class InstructorProfileSerializer(serializers.HyperlinkedModelSerializer):
    first_name = serializers.ReadOnlyField(source='user.first_name', allow_null=True)
    last_name = serializers.ReadOnlyField(source='user.last_name', allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Instructor
        fields = ('first_name', 'last_name','bio', 'image')

class InstructorRegisterSerializer(serializers.HyperlinkedModelSerializer, ValidateEmailMixin):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True)
    profile = InstructorProfileSerializer(source='instructor_info')
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'profile')

    
    def create(self, validated_data):
        # 1. Pop the nested profile data out
        profile_data = validated_data.pop('instructor_info')
        
        # 2. Create the User
        password = validated_data.pop('password')
        username = validated_data.get('username') or validated_data['email']

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.username = username
        user.save()

        # 3. Create the Instructor profile with the image
        Instructor.objects.create(user=user, **profile_data)
        
        return user


class LoginSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        if not user.is_active:
            raise serializers.ValidationError('User account is not active.')
        token = super().get_token(user)
        token['name'] = user.get_full_name()
        
        if hasattr(user, 'student_info'):
            token['role'] = 'student'
        elif hasattr(user, 'instructor_info'):
            token['role'] = 'instructor'
        elif user.is_superuser or user.is_staff:
            token['role'] = 'admin'
        else:
            token['role'] = 'unknown'
            
        return token
    

class GenerateOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.CharField()

class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    purpose = serializers.CharField()

class ResetPasswordSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    password = serializers.CharField() 

    def validate_password(self, value):
            validate_password(value)
            return value

class ActivateAccountSerializer(serializers.Serializer):
    otp_token = serializers.CharField()
    



# class StudentProfileView(serializers.ModelSerializer):
#     class Meta:
#         model = Student
#         fields = ('date_of_birth', 'title')

# class InstructorProfileView(serializers.ModelSerializer):
#     class Meta:
#         model = Instructor
#         fields = ('bio', 'image')


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()