from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, OrderViewSet, create_shop_checkout, public_products,
    upload_product_images, delete_product_image, reorder_product_images,
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('products/<int:product_id>/images/', upload_product_images, name='shop-upload-images'),
    path('products/<int:product_id>/images/<int:image_id>/', delete_product_image, name='shop-delete-image'),
    path('products/<int:product_id>/images/reorder/', reorder_product_images, name='shop-reorder-images'),
    path('checkout/', create_shop_checkout, name='shop-checkout'),
    path('public/products/', public_products, name='shop-public-products'),
]
