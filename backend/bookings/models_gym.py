"""
Gym/Fitness-specific models — ClassType and ClassSession (timetable).
Used when tenant.business_type == 'gym'.
"""
from django.db import models
from django.core.validators import MinValueValidator


WEEKDAY_CHOICES = [
    (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
    (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
]

DIFFICULTY_CHOICES = [
    ('beginner', 'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
    ('all', 'All Levels'),
]


class ClassType(models.Model):
    """A type of fitness class — e.g. Spin, Yoga, HIIT."""
    tenant = models.ForeignKey(
        'tenants.TenantSettings', on_delete=models.CASCADE, related_name='class_types'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=100, blank=True, default='', help_text='e.g. Cardio, Strength, Mind & Body')
    duration_minutes = models.IntegerField(default=45, validators=[MinValueValidator(5)])
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='all')
    max_capacity = models.IntegerField(default=20, validators=[MinValueValidator(1)])
    colour = models.CharField(max_length=7, blank=True, default='', help_text='Hex colour for timetable display')
    price_pence = models.IntegerField(default=0, help_text='Price per session in pence (0 = included in membership)')
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.duration_minutes}min, max {self.max_capacity})"


class ClassSession(models.Model):
    """A scheduled instance of a class on the weekly timetable."""
    tenant = models.ForeignKey(
        'tenants.TenantSettings', on_delete=models.CASCADE, related_name='class_sessions'
    )
    class_type = models.ForeignKey(ClassType, on_delete=models.CASCADE, related_name='sessions')
    instructor = models.ForeignKey(
        'bookings.Staff', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='class_sessions', help_text='Assigned instructor',
    )
    day_of_week = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=100, blank=True, default='', help_text='e.g. Studio 1, Main Hall')
    override_capacity = models.IntegerField(
        null=True, blank=True,
        help_text='Override class_type.max_capacity for this session',
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    @property
    def capacity(self):
        return self.override_capacity or self.class_type.max_capacity

    def __str__(self):
        day = dict(WEEKDAY_CHOICES).get(self.day_of_week, '?')
        return f"{self.class_type.name} — {day} {self.start_time:%H:%M}–{self.end_time:%H:%M}"
