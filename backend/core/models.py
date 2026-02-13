from django.db import models

from .models_auth import PasswordToken  # noqa: F401


class Config(models.Model):
    """Configuration key-value store for branding and feature flags"""
    
    CATEGORY_CHOICES = [
        ('branding', 'Branding'),
        ('features', 'Features'),
        ('system', 'System'),
    ]
    
    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='system')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'key']
        verbose_name = 'Configuration'
        verbose_name_plural = 'Configurations'
    
    def __str__(self):
        return f"{self.key} = {self.value}"
