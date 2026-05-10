from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .serializers import CouponApplySerializer
from .models import Coupon
from cart.models import Cart

class CouponView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    @action(detail=False, methods=['post'], serializer_class=CouponApplySerializer)
    def apply(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            try:
                coupon = Coupon.objects.get(code=code)
                if coupon.is_valid(request.user):
                    cart, _ = Cart.objects.get_or_create(user=request.user)
                    cart.coupon = coupon
                    cart.save()
                    # will be after payment
                    # CouponUsage.objects.create(user=request.user, coupon=coupon)
                    return Response({'message': 'Coupon applied successfully', 'discount': cart.discount()})
            except Coupon.DoesNotExist:
                return Response({'error': 'Invalid coupon code'}, status=400)
            except Exception as e:
                return Response({'error': str(e)}, status=400)
        else:
            return Response(serializer.errors, status=400)
        
    @action(detail=False, methods=['delete'])
    def remove(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
            cart.coupon = None
            cart.save()
            return Response({'message': 'Coupon removed successfully'})
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
                