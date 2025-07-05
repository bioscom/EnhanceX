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
#from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django_select2 import forms as s2forms
from widget_tweaks.templatetags.widget_tweaks import render_field

        
class DashboardForm(forms.ModelForm):
    class Meta:
        model = dashboards
        fields = ('name', 'description', 'filter', )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['filter'].queryset = SavedFilter.objects.all().order_by('name') # Force required in form
        self.fields['filter'].required = True
        
        
class ManagementReportForm(forms.ModelForm):
    class Meta:
        model = Functions
        fields = ['title', ]
        

class opexRecognitionForm(forms.ModelForm):
    recognition = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = opex_weekly_recognition
        fields = ['recognition', ]
        
class deliveryRecognitionForm(forms.ModelForm):
    recognition = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = delivery_weekly_recognition
        fields = ['recognition', ]
        
class capexRecognitionForm(forms.ModelForm):
    recognition = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = capex_weekly_Recognition
        fields = ['recognition', ]
        
class commercialRecognitionForm(forms.ModelForm):
    recognition = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = commercial_weekly_Recognition
        fields = ['recognition', ]
        
        
class ExcelUploadForm(forms.Form):
    file = forms.FileField()