from django.shortcuts import get_object_or_404

from rest_framework import generics, mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from cart.models import Cart, CartItem
from course.models import Course, Enrollment

from .models import Order
from .serializers import OrderSerializer


class OrderView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('coupon').prefetch_related('order_items')
    
    @action(detail=False, methods=['post'], serializer_class=None)
    def checkout(self, request):
        cart = get_object_or_404(
            Cart.objects.select_related('coupon').prefetch_related('items__course'),
             user=request.user
            )
        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=400)
        
        order = Order.objects.create(user=request.user,
                                    status=Order.Status.PENDING,
                                    coupon=cart.coupon,
                                    discount_amount=cart.discount())
        for item in cart.items.all():
            order.order_items.create(item=item.course, price=item.course.price)
        
        cart.items.all().delete()
        cart.coupon = None
        cart.delete()
        return Response({'message': 'Order created successfully', 'order_id': order.id}, status=201)


