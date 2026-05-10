from rest_framework import serializers



class OrderIdSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    