from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ConfigViewSet

router = DefaultRouter()
router.register(r'config', ConfigViewSet, basename='config')

urlpatterns = [
    path('', include(router.urls)),
]
