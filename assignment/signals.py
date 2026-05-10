from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from education.redis_client import r
from .models import Assignment, Question, MCQAnswer

def get_assignment_id(instance):
    if isinstance(instance, Assignment):
        return instance.id
    elif isinstance(instance, Question):
        return instance.assignment_id
    elif isinstance(instance, MCQAnswer):
        return instance.question.assignment_id
    return None

@receiver([post_save, post_delete], sender=Assignment)
@receiver([post_save, post_delete], sender=Question)
@receiver([post_save, post_delete], sender=MCQAnswer)
def invalidate_assignment_cache(sender, instance, **kwargs):
    assignment_id = get_assignment_id(instance)
    
    if assignment_id:
        r.delete(f"assignment:{assignment_id}")
