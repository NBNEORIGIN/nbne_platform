"""
Secure token model for password set/reset flows.
Tokens are single-use, time-limited (48h), and tied to a specific user.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class PasswordToken(models.Model):
    """One-time token for invite (set password) and password reset flows."""
    PURPOSE_CHOICES = [
        ('invite', 'Account Invite'),
        ('reset', 'Password Reset'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.purpose} token for {self.user.username} ({'used' if self.used else 'active'})"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=48)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    @classmethod
    def create_for_user(cls, user, purpose='invite', hours=48):
        """Create a new token, invalidating any existing unused tokens of the same purpose."""
        cls.objects.filter(user=user, purpose=purpose, used=False).update(used=True)
        return cls.objects.create(
            user=user,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(hours=hours),
        )
