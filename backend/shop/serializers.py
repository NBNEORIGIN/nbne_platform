from rest_framework import serializers
from .models import Product, ProductImage, Order, OrderItem


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'url', 'alt_text', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ''


class ProductSerializer(serializers.ModelSerializer):
    price_pence = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    primary_image_url = serializers.CharField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'subtitle', 'description', 'category',
            'price', 'compare_at_price', 'price_pence',
            'image_url', 'primary_image_url', 'images',
            'stock_quantity', 'track_stock', 'in_stock',
            'sort_order', 'active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    line_total_pence = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price_pence', 'line_total_pence']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_email', 'customer_phone',
            'status', 'total_pence', 'stripe_session_id', 'stripe_payment_intent',
            'notes', 'items', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
