from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def merge_session_cart(sender, request, user, **kwargs):
    from store.cart import merge_anonymous_cart

    merge_anonymous_cart(request, user)
