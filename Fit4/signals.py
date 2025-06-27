from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import *

# @receiver(pre_save, sender=Initiative)
# def generate_unique_slug(sender, instance, **kwargs):
#     if not instance.slug:
#         base_slug = slugify(instance.name)
#         slug = base_slug
#         counter = 1
#         while sender.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
#             slug = f"{base_slug}-{counter}"
#             counter += 1
#         instance.slug = slug


def generate_unique_slug(instance):
    base_slug = slugify(instance.initiative_name)
    slug = base_slug
    num = 1
    while Initiative.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f"{base_slug}-{num}"
        num += 1
    return slug

@receiver(pre_save, sender=Initiative)
def set_initiative_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = generate_unique_slug(instance)
