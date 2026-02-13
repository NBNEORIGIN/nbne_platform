from django.db import models
from .models import Staff

class BusinessHours(models.Model):
    """Business opening hours per day of week"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, unique=True)
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(default='09:00')
    close_time = models.TimeField(default='17:00')
    
    class Meta:
        ordering = ['day_of_week']
        verbose_name_plural = 'Business Hours'
    
    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        if not self.is_open:
            return f"{day_name}: Closed"
        return f"{day_name}: {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"


class StaffSchedule(models.Model):
    """Staff member working hours per day of week"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    is_working = models.BooleanField(default=True)
    start_time = models.TimeField(default='09:00')
    end_time = models.TimeField(default='17:00')
    break_minutes = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['staff', 'day_of_week']
        verbose_name = 'Staff Schedule'
    
    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        if not self.is_working:
            return f"{self.staff.name} - {day_name}: Not Working"
        return f"{self.staff.name} - {day_name}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class Closure(models.Model):
    """Business closures (holidays, special events)"""
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200)
    all_day = models.BooleanField(default=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        if self.all_day:
            return f"{self.date.strftime('%Y-%m-%d')}: {self.reason} (All Day)"
        return f"{self.date.strftime('%Y-%m-%d')}: {self.reason} ({self.start_time} - {self.end_time})"


class StaffLeave(models.Model):
    """Individual staff member time off"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='leave')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['start_date']
        verbose_name = 'Staff Leave'
        verbose_name_plural = 'Staff Leave'
    
    def __str__(self):
        if self.start_date == self.end_date:
            return f"{self.staff.name} - {self.start_date.strftime('%Y-%m-%d')}"
        return f"{self.staff.name} - {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"
