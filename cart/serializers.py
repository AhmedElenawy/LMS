from rest_framework import serializers

from .models import Cart, CartItem
from course.serializers import CourseListSerializer
from course.models import Course
from coupon.models import Coupon

class CartItemSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'course']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'discount', 'max_discount']

class CartSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        return obj.get_total_price()

    def get_discount_amount(self, obj):
        return obj.discount()

    def get_final_price(self, obj):
        return obj.get_total_price_after_discount()

    class Meta:
        model = Cart
        fields = ['id', 'created_at', 'total_price', 'discount_amount', 'final_price', 'items', 'coupon']


class CartCourseIdSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
