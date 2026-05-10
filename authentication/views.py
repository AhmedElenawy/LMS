from rest_framework.views import APIView

from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework.response import Response
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from .permissions import IsProfileOwner, IsStudent, IsInstructor
from .models import Student, Instructor
from .serializers import (LoginSerializer,StudentRegisterSerializer,
                          InstructorRegisterSerializer,
                           GenerateOtpSerializer, VerifyOtpSerializer,
                           ResetPasswordSerializer, ActivateAccountSerializer,
                           StudentProfileSerializer, InstructorProfileSerializer,
                           LogoutSerializer)
from .otp import Otp

class StudentRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = StudentRegisterSerializer

class InstructorRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = InstructorRegisterSerializer
    parser_classes = (MultiPartParser, FormParser)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            refresh = serializer.validated_data['refresh']
            try:
                token = RefreshToken(refresh)
                token.blacklist()
                return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    CLIENT_ID = settings.GOOGLE_CLIENT_ID


    def post(self, request):
        token = request.data.get('token')
        role = request.data.get('role', 'student')

        if not token:
            return Response({"error": "No credentials found"}, status=400)
        
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), self.CLIENT_ID)
            if not idinfo.get("email_verified", False):
                return Response({"error": "Google email is not verified"}, status=400)
            
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            username = email
        except ValueError:
            return Response({'error': 'Invalid Google token or token expired'}, status=401)
        
        try:
            user = User.objects.get(email__iexact=email)
            created = False
            
        except User.DoesNotExist:
            with transaction.atomic():
                user = User(username=username, email=email, first_name=first_name, last_name=last_name)
                user.save()
                created = True
                if role == 'student':
                    Student.objects.create(user=user)
                elif role == 'instructor':
                    Instructor.objects.create(user=user)

        refresh = LoginSerializer.get_token(user)

        return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'is_new_user': created,
                'message': 'Google Login successful'
            }, status=200)


class GenerateOTPView(APIView):
    permission_classes = [AllowAny]
    serializer_class = GenerateOtpSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            purpose = serializer.validated_data['purpose']

            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                return Response({'error': 'email does not exist'}, status=400)
            
            if not user.is_active and purpose == 'password_reset':
                return Response({'error': 'User account is not active.'}, status=400)
            
            try:  
                Otp(email=email, purpose=purpose).send_otp()
                return Response({'message': 'OTP sent successfully',
                                 'email': serializer.validated_data['email']}, status=200)
            except Exception as e:
                return Response({'error': str(e)}, status=400)
        else:
            return Response(serializer.errors, status=400)
            
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOtpSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            purpose = serializer.validated_data['purpose']
            otp = serializer.validated_data['otp']

            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                return Response({'error': 'email does not exist'}, status=400)
            
            if not user.is_active and purpose == 'password_reset':
                return Response({'error': 'User account is not active.'}, status=400)
            
            try:
                Otp(email=email, purpose=purpose).validate_otp(otp)
                signer = TimestampSigner()
                payload = {
                    'user_id': user.id,
                    'purpose': purpose,
                }
                reset_token = signer.sign_object(payload)
                return Response({'message': 'OTP verified successfully',
                                 'otp_token': reset_token}, status=200)
            except Exception as e:
                return Response({'error': str(e)}, status=400)
            
        else:
            return Response(serializer.errors, status=400)
    

class CheckOtpTokenMixin:
    def check_otp_token(self, otp_token, purpose):
        signer = TimestampSigner()

        try:
            # 1. Unsign the token.
            # max_age=900 means this token strictly expires after 900 seconds (15 minutes).
            payload = signer.unsign_object(otp_token, max_age=900)
            
            # 2. Verify the purpose (prevents token swapping)
            if payload.get('purpose') != purpose:
                raise ValidationError({'error': 'Invalid token purpose'})
                
            return payload.get('user_id')

        except SignatureExpired:
            raise ValidationError({'error': 'Reset token has expired. Please request a new OTP.'})
            
        except BadSignature:
            raise ValidationError({'error': 'Invalid reset token.'})
            


class ResetPasswordView(APIView, CheckOtpTokenMixin):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            otp_token = serializer.validated_data['otp_token']
            password = serializer.validated_data['password']
            try:
                user_id = self.check_otp_token(otp_token, 'password_reset') 
            except ValidationError as e:
                return Response(e.detail, status=400)
            try:
                user = User.objects.get(id=user_id)
                user.set_password(password)
                user.save()
                return Response({'message': 'Password reset successfully',
                                 'user_id': user_id}, status=200)
            except Exception as e:
                return Response({'error': str(e)}, status=400)
        else:
            return Response(serializer.errors, status=400)

class ActivateAccountView(APIView, CheckOtpTokenMixin):
    permission_classes = [AllowAny]
    serializer_class = ActivateAccountSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            otp_token = serializer.validated_data['otp_token']
            try:
                user_id = self.check_otp_token(otp_token, 'account_activation')
            except ValidationError as e:
                return Response(e.detail, status=400)
            try:
                user = User.objects.get(id=user_id)
                if user.is_active:
                    return Response({'message': 'Account already active'}, status=200)
                user.is_active = True
                user.save()
                return Response({'message': 'Account activated successfully'}, status=200)
            except Exception as e:
                return Response({'error': str(e)}, status=400)
        else:
            return Response(serializer.errors, status=400)
        

class StudentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    def get_object(self):
        return self.request.user.student_info

class InstructorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = InstructorProfileSerializer
    permission_classes = [IsAuthenticated, IsInstructor]
    def get_object(self):
        return self.request.user.instructor_info
    