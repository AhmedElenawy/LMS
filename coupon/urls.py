from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CouponView

app_name = 'coupon'

router = DefaultRouter()
router.register(r'coupon', CouponView, basename='coupon-apply')

urlpatterns = [
    path('', include(router.urls))
]
