"""
Serializers for Payment Integration
"""
from rest_framework import serializers
from .models_payment import ClassPackage, ClientCredit, PaymentTransaction


class ClassPackageSerializer(serializers.ModelSerializer):
    """Serializer for ClassPackage"""
    
    price_per_class = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassPackage
        fields = [
            'id',
            'name',
            'description',
            'class_count',
            'price',
            'price_per_class',
            'validity_days',
            'active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'price_per_class']
    
    def get_price_per_class(self, obj):
        return float(obj.price_per_class)


class ClientCreditSerializer(serializers.ModelSerializer):
    """Serializer for ClientCredit"""
    
    package_name = serializers.CharField(source='package.name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = ClientCredit
        fields = [
            'id',
            'client',
            'package',
            'package_name',
            'total_classes',
            'remaining_classes',
            'payment_id',
            'amount_paid',
            'purchased_at',
            'expires_at',
            'active',
            'is_expired',
            'is_valid',
        ]
        read_only_fields = ['id', 'purchased_at', 'is_expired', 'is_valid']
    
    def get_is_expired(self, obj):
        return obj.is_expired
    
    def get_is_valid(self, obj):
        return obj.is_valid


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for PaymentTransaction"""
    
    client_name = serializers.CharField(source='client.name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True, allow_null=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id',
            'client',
            'client_name',
            'transaction_type',
            'status',
            'payment_system_id',
            'amount',
            'currency',
            'package',
            'package_name',
            'credit',
            'payment_metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
