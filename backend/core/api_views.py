from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Config
from .serializers import ConfigSerializer


class ConfigViewSet(viewsets.ModelViewSet):
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get all config entries grouped by category"""
        categories = {}
        for config in Config.objects.all():
            if config.category not in categories:
                categories[config.category] = {}
            categories[config.category][config.key] = config.value
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def branding(self, request):
        """Get branding configuration"""
        branding = {}
        for config in Config.objects.filter(category='branding'):
            branding[config.key.replace('branding.', '')] = config.value
        return Response(branding)
    
    @action(detail=False, methods=['get'])
    def features(self, request):
        """Get feature flags"""
        features = {}
        for config in Config.objects.filter(category='features'):
            features[config.key.replace('features.', '')] = config.value
        return Response(features)
