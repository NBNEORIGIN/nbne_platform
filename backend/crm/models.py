from django.db import models
from django.utils import timezone


class Lead(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('QUALIFIED', 'Qualified'),
        ('CONVERTED', 'Converted'),
        ('LOST', 'Lost'),
    ]
    SOURCE_CHOICES = [
        ('booking', 'Booking'),
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('social', 'Social Media'),
        ('manual', 'Manual Entry'),
        ('other', 'Other'),
    ]

    tenant = models.ForeignKey('tenants.TenantSettings', on_delete=models.CASCADE, related_name='leads')
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='manual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    value_pence = models.IntegerField(default=0, help_text='Estimated value in pence')
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags e.g. VIP,Lapsed')
    follow_up_date = models.DateField(null=True, blank=True)
    last_contact_date = models.DateField(null=True, blank=True)
    marketing_consent = models.BooleanField(default=False, help_text='GDPR marketing consent')
    # Link to booking client if auto-created
    client_id = models.IntegerField(null=True, blank=True, help_text='bookings.Client FK')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.status})'

    @property
    def client_score(self):
        """Deterministic score: CONVERTED=100, QUALIFIED=70, CONTACTED=40, NEW=10, LOST=0"""
        return {'CONVERTED': 100, 'QUALIFIED': 70, 'CONTACTED': 40, 'NEW': 10, 'LOST': 0}.get(self.status, 0)

    @property
    def client_score_label(self):
        s = self.client_score
        if s >= 70:
            return 'High'
        if s >= 30:
            return 'Medium'
        return 'Low'

    @property
    def action_required(self):
        """Deterministic next action based on status + follow-up date."""
        if self.status == 'CONVERTED':
            return None
        if self.status == 'LOST':
            return None
        if self.status == 'NEW':
            return 'Contact'
        if self.status == 'QUALIFIED':
            return 'Convert'
        # CONTACTED
        if self.follow_up_date:
            today = timezone.now().date()
            if self.follow_up_date < today:
                days_over = (today - self.follow_up_date).days
                if days_over >= 7:
                    return 'Follow up overdue'
                return 'Follow up overdue'
            if self.follow_up_date == today:
                return 'Follow up today'
            return 'Follow up'
        return 'Follow up'

    @property
    def sort_priority(self):
        """Lower number = more important. Used for default sort."""
        today = timezone.now().date()
        if self.follow_up_date and self.follow_up_date < today:
            return 0  # overdue
        if self.follow_up_date and self.follow_up_date == today:
            return 1  # today
        return {'QUALIFIED': 2, 'NEW': 3, 'CONTACTED': 4, 'CONVERTED': 8, 'LOST': 9}.get(self.status, 5)


class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='lead_notes')
    text = models.TextField()
    created_by = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Note on {self.lead.name} at {self.created_at}'


class LeadMessage(models.Model):
    TYPE_CHOICES = [
        ('email_in', 'Email Received'),
        ('email_out', 'Email Sent'),
        ('call', 'Phone Call'),
        ('sms', 'SMS'),
        ('note', 'Note'),
    ]
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='note')
    subject = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    created_by = models.CharField(max_length=200, blank=True)
    # AI-parsed metadata (populated when using email analyzer)
    ai_parsed = models.JSONField(null=True, blank=True, help_text='AI-extracted fields from email')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.get_message_type_display()} on {self.lead.name}'


class LeadHistory(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=200)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.lead.name}: {self.action}'
