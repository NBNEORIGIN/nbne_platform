"""
Intake Profile Model for NBNE Business Platform
GDPR-compliant, no medical/diagnostic data collection
"""
from django.db import models
from django.core.validators import EmailValidator


class IntakeProfile(models.Model):
    """
    One-time intake profile for wellness session participants.
    Collected before first booking, reused for subsequent bookings.
    GDPR-safe: No medical, diagnostic, or sensitive health data.
    """
    
    # Core Identity
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=20)
    
    # Emergency Contact (Safety requirement)
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(max_length=20)
    
    # Session Preferences (Optional, non-medical)
    experience_level = models.CharField(
        max_length=50,
        blank=True,
        help_text='e.g., First time, Some experience, Regular practitioner'
    )
    goals = models.TextField(
        blank=True,
        help_text='What would you like to achieve from your sessions? (Optional)'
    )
    preferences = models.TextField(
        blank=True,
        help_text='Any preferences or notes for your facilitator? (Optional)'
    )
    
    # GDPR Consent Fields
    consent_booking = models.BooleanField(
        default=False,
        help_text='Consent to book sessions and store booking data'
    )
    consent_marketing = models.BooleanField(
        default=False,
        help_text='Consent to receive updates and wellness information'
    )
    consent_privacy = models.BooleanField(
        default=False,
        help_text='Confirmed reading and accepting privacy policy'
    )
    
    # Disclaimer version signed
    disclaimer_version = models.ForeignKey(
        'IntakeWellbeingDisclaimer',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='signed_profiles',
        help_text='Which disclaimer version was signed'
    )
    renewal_required = models.BooleanField(
        default=False,
        help_text='Owner has flagged this client to re-sign on next booking'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(
        default=False,
        help_text='Intake form completed and validated'
    )
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date when questionnaire was completed'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Expiry date (1 year from completion) - must be renewed annually'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Intake Profile'
        verbose_name_plural = 'Intake Profiles'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['completed']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def is_expired(self):
        """Check if questionnaire has expired (older than 1 year)"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid_for_booking(self):
        """Check if intake is complete, consents given, not expired, and not flagged for renewal"""
        return (
            self.completed and
            self.consent_booking and
            self.consent_privacy and
            self.full_name and
            self.email and
            self.phone and
            self.emergency_contact_name and
            self.emergency_contact_phone and
            not self.is_expired() and
            not self.renewal_required
        )
    
    def save(self, *args, **kwargs):
        """Auto-mark as completed if all required fields present and set expiry"""
        from django.utils import timezone
        from datetime import timedelta
        
        if (self.full_name and self.email and self.phone and
            self.emergency_contact_name and self.emergency_contact_phone and
            self.consent_booking and self.consent_privacy):
            
            # Mark as completed and update dates (even if already completed - for renewals)
            self.completed = True
            self.completed_date = timezone.now()
            # Always set expiry to 1 year from now (for renewals)
            self.expires_at = self.completed_date + timedelta(days=365)
        
        super().save(*args, **kwargs)


class IntakeWellbeingDisclaimer(models.Model):
    """
    Wellbeing disclaimer text shown during intake.
    Editable via admin, versioned for compliance.
    """
    version = models.CharField(max_length=20, unique=True)
    content = models.TextField(
        help_text='Disclaimer text shown to users during intake'
    )
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wellbeing Disclaimer'
        verbose_name_plural = 'Wellbeing Disclaimers'
    
    def __str__(self):
        return f"Disclaimer v{self.version} ({'Active' if self.active else 'Inactive'})"
    
    def save(self, *args, **kwargs):
        """Ensure only one active disclaimer"""
        if self.active:
            IntakeWellbeingDisclaimer.objects.filter(active=True).update(active=False)
        super().save(*args, **kwargs)
