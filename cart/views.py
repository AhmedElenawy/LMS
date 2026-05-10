from django.shortcuts import get_object_or_404

from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart, CartItem
from course.models import Course, Enrollment
from .serializers import CartSerializer, CartCourseIdSerializer


class CartView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_cart(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    def get_cart_detail(self, request):
        cart, _ = Cart.objects.select_related('coupon').prefetch_related(
            'items__course',
            'items__course__instructor__user',
            'items__course__category'
        ).get_or_create(user=request.user)
        return cart

    @action(detail=False, methods=['get'], serializer_class=CartSerializer)
    def cart(self, request):
        cart = self.get_cart_detail(request)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], serializer_class=CartCourseIdSerializer)
    def add(self, request):
        data = self.get_serializer(data=request.data)
        if data.is_valid():
            course_id = data.validated_data['course_id']
            course = get_object_or_404(Course, id=course_id)
            cart = self.get_cart(request)
            if CartItem.objects.filter(cart=cart, course=course).exists():
                return Response({'error': 'Course already in cart'}, status=400)
            
            if hasattr(request.user, 'student_info'):
                if Enrollment.objects.filter(student=request.user.student_info, course=course).exists():
                    return Response({'error': 'Already enrolled in this course'}, status=400)
            else:
                return Response({'error': 'User is not a student'}, status=400)
            
            CartItem.objects.create(cart=cart, course=course)
            return Response({'message': 'Course added to cart'}, status=201)
        else:
            return Response(data.errors, status=400)
        

    @action(detail=False, methods=['delete', 'post'], serializer_class=CartCourseIdSerializer)
    def remove(self, request):
        data = self.get_serializer(data=request.data)
        if data.is_valid():
            course_id = data.validated_data['course_id']
            course = get_object_or_404(Course, id=course_id)
            cart = self.get_cart(request)
            try:
                cart_item = CartItem.objects.get(cart=cart, course=course)
                cart_item.delete()
                return Response({'message': 'Course removed from cart'}, status=200)
            except CartItem.DoesNotExist:
                return Response({'error': 'Course not in cart'}, status=400)
        else:
            return Response(data.errors, status=400)

