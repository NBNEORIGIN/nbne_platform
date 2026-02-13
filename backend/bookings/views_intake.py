"""
API Views for Intake Profile
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models_intake import IntakeProfile, IntakeWellbeingDisclaimer
from .serializers_intake import IntakeProfileSerializer, IntakeWellbeingDisclaimerSerializer


class IntakeProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for IntakeProfile
    
    Endpoints:
    - GET /api/intake/ - List all profiles (admin)
    - POST /api/intake/ - Create new profile or update existing
    - GET /api/intake/{id}/ - Retrieve profile
    - PUT /api/intake/{id}/ - Update profile
    - GET /api/intake/status/?email=x - Check if email has completed intake
    """
    queryset = IntakeProfile.objects.all()
    serializer_class = IntakeProfileSerializer
    
    def create(self, request, *args, **kwargs):
        """Create or update intake profile based on email"""
        email = request.data.get('email')
        if email:
            # Check if profile exists
            existing = IntakeProfile.objects.filter(email=email).first()
            if existing:
                # Update existing profile
                serializer = self.get_serializer(existing, data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
        
        # Create new profile
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Check intake status by email
        GET /api/intake/status/?email=user@example.com
        
        Returns:
        - exists: boolean
        - completed: boolean
        - profile_id: int (if exists)
        - is_valid_for_booking: boolean
        """
        email = request.query_params.get('email')
        
        if not email:
            return Response(
                {'error': 'Email parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            profile = IntakeProfile.objects.get(email=email)
            return Response({
                'exists': True,
                'completed': profile.completed,
                'profile_id': profile.id,
                'is_valid_for_booking': profile.is_valid_for_booking(),
            })
        except IntakeProfile.DoesNotExist:
            return Response({
                'exists': False,
                'completed': False,
                'profile_id': None,
                'is_valid_for_booking': False,
            })
    
    @action(detail=False, methods=['get'])
    def by_email(self, request):
        """
        Get full profile by email
        GET /api/intake/by_email/?email=user@example.com
        """
        email = request.query_params.get('email')
        
        if not email:
            return Response(
                {'error': 'Email parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile = get_object_or_404(IntakeProfile, email=email)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def expire(self, request, pk=None):
        """
        Manually expire a specific intake profile
        POST /api/intake-profiles/{id}/expire/
        """
        profile = self.get_object()
        from django.utils import timezone
        profile.expires_at = timezone.now()
        profile.save()
        return Response({
            'message': f'Intake form expired for {profile.full_name}',
            'expired': True
        })
    
    @action(detail=False, methods=['post'])
    def expire_all(self, request):
        """
        Manually expire all intake profiles
        POST /api/intake/expire_all/
        """
        from django.utils import timezone
        count = IntakeProfile.objects.filter(completed=True).update(
            expires_at=timezone.now()
        )
        return Response({
            'message': f'Expired {count} intake forms',
            'count': count
        })

    @action(detail=True, methods=['post'])
    def require_renewal(self, request, pk=None):
        """
        Flag a single client to re-sign on next booking
        POST /api/intake/{id}/require_renewal/
        """
        profile = self.get_object()
        profile.renewal_required = True
        profile.save(update_fields=['renewal_required'])
        return Response({
            'message': f'Renewal required for {profile.full_name}',
            'renewal_required': True
        })

    @action(detail=True, methods=['post'])
    def clear_renewal(self, request, pk=None):
        """
        Clear renewal flag for a single client
        POST /api/intake/{id}/clear_renewal/
        """
        profile = self.get_object()
        profile.renewal_required = False
        profile.save(update_fields=['renewal_required'])
        return Response({
            'message': f'Renewal cleared for {profile.full_name}',
            'renewal_required': False
        })


class IntakeWellbeingDisclaimerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Wellbeing Disclaimer
    
    Endpoints:
    - GET /api/intake-disclaimer/ - List disclaimers
    - POST /api/intake-disclaimer/ - Create new disclaimer (admin)
    - GET /api/intake-disclaimer/active/ - Get active disclaimer
    """
    queryset = IntakeWellbeingDisclaimer.objects.all()
    serializer_class = IntakeWellbeingDisclaimerSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get the currently active disclaimer"""
        try:
            disclaimer = IntakeWellbeingDisclaimer.objects.get(active=True)
            serializer = self.get_serializer(disclaimer)
            return Response(serializer.data)
        except IntakeWellbeingDisclaimer.DoesNotExist:
            return Response(
                {'error': 'No active disclaimer found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def require_renewal(self, request, pk=None):
        """
        Activate this disclaimer and flag all clients who signed an older version
        (or no version) to re-sign on their next booking.
        POST /api/intake-disclaimer/{id}/require_renewal/
        """
        disclaimer = self.get_object()
        # Activate this version (deactivates others via model save)
        disclaimer.active = True
        disclaimer.save()
        # Flag all completed profiles that signed a different (or no) version
        count = IntakeProfile.objects.filter(completed=True).exclude(
            disclaimer_version=disclaimer
        ).update(renewal_required=True)
        return Response({
            'message': f'Disclaimer v{disclaimer.version} activated. {count} client(s) flagged for renewal.',
            'count': count,
            'version': disclaimer.version,
        })
