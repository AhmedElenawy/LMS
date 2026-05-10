from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartView

app_name = 'cart'

router = DefaultRouter()
router.register(r'cart', CartView, basename='cart')

urlpatterns = [
    path('', include(router.urls))
]