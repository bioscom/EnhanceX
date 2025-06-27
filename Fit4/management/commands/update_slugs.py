from django.core.management.base import BaseCommand
from django.utils.text import slugify
from Fit4.models import *

class Command(BaseCommand):
    help = "Generate unique slugs for all YourModel records"

    def handle(self, *args, **kwargs):
        for obj in Initiative.objects.all():
            base_slug = slugify(obj.initiative_name)
            slug = base_slug
            counter = 1

            # Ensure uniqueness
            while Initiative.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            if obj.slug != slug:
                obj.slug = slug
                obj.save()
                self.stdout.write(self.style.SUCCESS(f"Updated slug for ID {obj.pk}: {slug}"))
