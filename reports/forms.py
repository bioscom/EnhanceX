from django import forms
from django.urls import reverse_lazy
from .models import * 
from django.forms import ClearableFileInput, formset_factory
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm as UserCreationFormBase
from datetime import datetime
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from bootstrap_datepicker_plus.widgets import DatePickerInput
#from django_ckeditor_5.widgets import CKEditor5Widget
#from ckeditor.widgets import CKEditorWidget
#from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django_select2 import forms as s2forms
from widget_tweaks.templatetags.widget_tweaks import render_field


class CategoryForm(forms.ModelForm):
    class Meta:
        model = report_category
        fields = ('category',)
        
        labels = {
            'category': 'category',
        }
        
class SavedFilterForm(forms.ModelForm):
    class Meta:
        model = SavedFilter
        fields = ('name', 'category',)


# created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
#     name = models.CharField(max_length=255)
#     category = models.ForeignKey(report_category, on_delete=models.CASCADE, related_name='SavedFilter_category')
#     unique_name = models.CharField(max_length=250)
#     description = models.TextField(null=True, blank=True)
#     filter_params = models.TextField(null=True, blank=True)

# class ReportForm(forms.ModelForm):
#     class Meta:
#         model = report
#         fields = ('name', 'category', 'description', 'unique_name', 'WorkStream', 'wsFilters', 'overall_status', 'osFilters', 'discipline',
#         'discFilters', 'Function', 'funcFilters', 'SavingType', 'stFilters', 'Plan_Relevance', 'psFilters', 'HashTag', 'htFilters')
    
#     # workStreamSponsor = models.TextField(blank=True, null=True)
#     # workStreamLead = models.TextField(blank=True, null=True)
#     # financeSponsor = models.TextField(blank=True, null=True)
#     # initiativeSponsor = models.TextField(blank=True, null=True)
#     # initiativeOwner = models.TextField(blank=True, null=True)
        
        
# class ReportForm2(forms.ModelForm):
#     class Meta:
#         model = report
#         #fields = ('name', 'category', 'description', )
#         fields = ('name', 'category', 'unique_name', 'description', )
