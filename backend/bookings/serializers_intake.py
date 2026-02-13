"""
Serializers for Intake Profile API
"""
from rest_framework import serializers
from .models_intake import IntakeProfile, IntakeWellbeingDisclaimer


class IntakeProfileSerializer(serializers.ModelSerializer):
    """Serializer for IntakeProfile with validation"""
    
    is_valid_for_booking = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    disclaimer_version_str = serializers.SerializerMethodField()
    
    class Meta:
        model = IntakeProfile
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'emergency_contact_name',
            'emergency_contact_phone',
            'experience_level',
            'goals',
            'preferences',
            'consent_booking',
            'consent_marketing',
            'consent_privacy',
            'disclaimer_version',
            'disclaimer_version_str',
            'renewal_required',
            'completed',
            'completed_date',
            'expires_at',
            'is_valid_for_booking',
            'is_expired',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'completed', 'completed_date', 'expires_at', 'created_at', 'updated_at', 'is_valid_for_booking', 'is_expired', 'disclaimer_version_str']
    
    def get_is_valid_for_booking(self, obj):
        return obj.is_valid_for_booking()
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_disclaimer_version_str(self, obj):
        if obj.disclaimer_version:
            return f'v{obj.disclaimer_version.version}'
        return None
    
    def validate_email(self, value):
        """Ensure email is unique for new profiles"""
        # Skip validation if updating existing instance
        if self.instance is not None:
            return value
            
        # For new profiles, check if email already exists
        if IntakeProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "An intake profile with this email already exists. Please use a different email."
            )
        return value
    
    def validate(self, data):
        """Validate required consents"""
        if not data.get('consent_booking'):
            raise serializers.ValidationError({
                'consent_booking': 'You must consent to booking to proceed.'
            })
        if not data.get('consent_privacy'):
            raise serializers.ValidationError({
                'consent_privacy': 'You must accept the privacy policy to proceed.'
            })
        return data


class IntakeWellbeingDisclaimerSerializer(serializers.ModelSerializer):
    """Serializer for wellbeing disclaimer"""
    signed_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IntakeWellbeingDisclaimer
        fields = ['id', 'version', 'content', 'active', 'created_at', 'signed_count']
        read_only_fields = ['id', 'created_at', 'signed_count']
    
    def get_signed_count(self, obj):
        return obj.signed_profiles.count()
