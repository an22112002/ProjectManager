from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, SupportChat

@receiver(post_save, sender=User)
def create_SupportChat(sender, instance, created, **kwargs):
    if created:
        SupportChat.objects.create(Id_user=instance)