"""
Payment Integration Models for NBNE Business Platform
Supports class packages and credit tracking
"""
from django.db import models
from django.core.validators import MinValueValidator


class ClassPackage(models.Model):
    """
    Class packages that clients can purchase
    e.g., "5 Class Pass", "10 Class Pass", "Monthly Unlimited"
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    class_count = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Number of classes included in this package'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    validity_days = models.IntegerField(
        default=365,
        help_text='Number of days until package expires after purchase'
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_count']
        verbose_name = 'Class Package'
        verbose_name_plural = 'Class Packages'
    
    def __str__(self):
        return f"{self.name} ({self.class_count} classes - £{self.price})"
    
    @property
    def price_per_class(self):
        """Calculate price per class"""
        return self.price / self.class_count if self.class_count > 0 else 0


class ClientCredit(models.Model):
    """
    Track client's remaining class credits from purchased packages
    """
    client = models.ForeignKey('bookings.Client', on_delete=models.CASCADE, related_name='credits')
    package = models.ForeignKey(
        ClassPackage,
        on_delete=models.PROTECT,
        related_name='client_credits',
        null=True,
        blank=True,
        help_text='Package that generated these credits'
    )
    
    # Credit tracking
    total_classes = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text='Total classes in this credit package'
    )
    remaining_classes = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text='Classes remaining to be used'
    )
    
    # Payment reference
    payment_id = models.CharField(
        max_length=200,
        blank=True,
        help_text='Payment system reference for this purchase'
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount paid for this package'
    )
    
    # Validity
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text='Date when unused credits expire'
    )
    active = models.BooleanField(
        default=True,
        help_text='Whether credits can still be used'
    )
    
    class Meta:
        ordering = ['-purchased_at']
        verbose_name = 'Client Credit'
        verbose_name_plural = 'Client Credits'
    
    def __str__(self):
        return f"{self.client.name} - {self.remaining_classes}/{self.total_classes} classes remaining"
    
    @property
    def is_expired(self):
        """Check if credits have expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if credits can be used"""
        return self.active and self.remaining_classes > 0 and not self.is_expired
    
    def use_credit(self):
        """Use one credit, returns True if successful"""
        if self.is_valid:
            self.remaining_classes -= 1
            if self.remaining_classes == 0:
                self.active = False
            self.save()
            return True
        return False
    
    def refund_credit(self):
        """Refund one credit (e.g., booking cancelled)"""
        if self.remaining_classes < self.total_classes:
            self.remaining_classes += 1
            self.active = True
            self.save()
            return True
        return False


class PaymentTransaction(models.Model):
    """
    Log of all payment transactions for audit trail
    Links to external payment system
    """
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Package Purchase'),
        ('single', 'Single Class Purchase'),
        ('refund', 'Refund'),
    ]
    
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    client = models.ForeignKey('bookings.Client', on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    
    # Payment system reference
    payment_system_id = models.CharField(
        max_length=200,
        unique=True,
        help_text='Unique ID from payment system (e.g., Stripe payment intent ID)'
    )
    
    # Transaction details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GBP')
    
    # Related records
    package = models.ForeignKey(
        ClassPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Package purchased (if applicable)'
    )
    credit = models.ForeignKey(
        ClientCredit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Credit record created (if applicable)'
    )
    
    # Metadata
    payment_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional payment data from payment system'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_system_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.transaction_type} - £{self.amount} ({self.status})"
