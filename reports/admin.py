from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(report_category)
admin.site.register(SavedFilter)
