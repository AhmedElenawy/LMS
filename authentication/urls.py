from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authentication'

urlpatterns = [
    path('students/register/', views.StudentRegisterView.as_view(), name='student_list_create'),
    path('students/me/', views.StudentProfileView.as_view(), name='student_profile'),
    path('instructors/register/', views.InstructorRegisterView.as_view(), name='instructor_list_create'),
    path('instructors/me/', views.InstructorProfileView.as_view(), name='instructor_profile'),
    path('auth/token/', views.LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/google/', views.GoogleAuthView.as_view(), name='google_auth'),
    path('auth/otp/', views.GenerateOTPView.as_view(), name='generate_otp'),
    path('auth/otp/verify/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('auth/passwords/reset/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('auth/accounts/activate/', views.ActivateAccountView.as_view(), name='activate_account'),
]