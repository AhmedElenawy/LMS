from django.shortcuts import get_object_or_404
from decimal import Decimal
import stripe
from django.urls import reverse
from django.conf import settings

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from order.models import Order
from .serializers import OrderIdSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

class PaymentProcessView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderIdSerializer

    def post(self, request):
        data = self.serializer_class(data=request.data)
        if data.is_valid():
            order_id = data.validated_data['order_id']
            order = get_object_or_404(Order.objects.prefetch_related('order_items__item')
                                      , id=order_id, user=request.user,)
            if order.status != Order.Status.PENDING:
                return Response({'error': 'Order is not pending'}, status=400)
            success_url = f"{settings.FRONTEND_URL}/payment/success"
            cancel_url = f"{settings.FRONTEND_URL}/payment/cancel"
            session_data = {
                'mode': 'payment',
                'client_reference_id': order.id,
                'success_url': success_url,
                'cancel_url': cancel_url,
                'line_items': [],
            }
            for item in order.order_items.all():
                session_data['line_items'].append({
                    'price_data': {
                        'product_data': {
                            'name': item.item.title,
                        },
                        'unit_amount': int(item.price * Decimal('100')),
                        'currency': 'usd',
                    },
                    'quantity': 1,
                })
            if order.coupon:
                stripe_coupon = stripe.Coupon.create(
                    name=order.coupon.code,
                    amount_off=int(order.discount_amount * 100),
                    duration='once',
                    currency='usd'
                )
                session_data['discounts'] = [{'coupon': stripe_coupon.id}]
            
            session = stripe.checkout.Session.create(**session_data)
            order.session_id = session.id
            order.save()
            return Response({'url': session.url}, status=200)
                   
        else:
            return Response(data.errors, status=400)
        

class payment_success(APIView):
    def get(self, request):
        return Response({'message': 'Payment successful'}, status=200)

class payment_cancel(APIView):
    def get(self, request):
        return Response({'message': 'Payment cancelled'}, status=200)

