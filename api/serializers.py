from rest_framework import serializers
from .models import User, CurrencyRate, Order, CartItem, Notification

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'shams_id', 'is_verified', 'created_at']
        read_only_fields = ['id', 'shams_id', 'is_verified', 'created_at']

class PhoneLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6)

class SyncUserSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    shams_id = serializers.CharField(max_length=10, required=False)

class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = '__all__'

class CalculatePriceSerializer(serializers.Serializer):
    price_yuan = serializers.DecimalField(max_digits=10, decimal_places=2)
    weight_kg = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class CartItemSerializer(serializers.ModelSerializer):
    total_tmt = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'product_name', 'product_image', 'price_yuan', 'price_tmt', 'quantity', 'total_tmt', 'created_at']
    
    def get_total_tmt(self, obj):
        return float(obj.get_total_tmt())

class NotificationSerializer(serializers.ModelSerializer):
    formatted_date = serializers.SerializerMethodField(read_only=True)
    formatted_time = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'notification_type', 'is_read', 'created_at', 'formatted_date', 'formatted_time']
        read_only_fields = ['id', 'created_at']
    
    def get_formatted_date(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')
    
    def get_formatted_time(self, obj):
        return obj.created_at.strftime('%H:%M')