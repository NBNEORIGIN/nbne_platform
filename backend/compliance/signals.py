from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender='compliance.ComplianceItem')
def recalculate_score_on_save(sender, instance, **kwargs):
    from .models import PeaceOfMindScore
    PeaceOfMindScore.recalculate()


@receiver(post_delete, sender='compliance.ComplianceItem')
def recalculate_score_on_delete(sender, instance, **kwargs):
    from .models import PeaceOfMindScore
    PeaceOfMindScore.recalculate()
