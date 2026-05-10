from rest_framework import serializers
from .models import Order, OrderItems

from course.serializers import CourseListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    item = CourseListSerializer(read_only=True)
    class Meta:
        model = OrderItems
        fields = ['id', 'item', 'price']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    coupon_code = serializers.ReadOnlyField(source='coupon.code')
    total_price = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    payment_url = serializers.SerializerMethodField()
    def get_total_price(self, obj):
        return obj.get_total_price()

    def get_final_price(self, obj):
        return obj.get_total_price_after_discount()
    def get_payment_url(self, obj):
        return obj.get_payment_url()
    class Meta:
        model = Order
        fields = ['id', 'status', 'created','updated',
                   'discount_amount', 'coupon_code',
                   'total_price','final_price', 'order_items', 'payment_url']
        

