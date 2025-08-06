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
    
    

class deliveryTargetForm(forms.ModelForm):
    class Meta:
        model = delivery_target
        fields = ['target']
        widgets = {
            'target': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['YYear'].queryset = delivery_target.objects.values_list('YYear', flat=True).distinct().order_by('YYear')
        

class opexTargetForm(forms.ModelForm):
    class Meta:
        model = opex_target
        fields = ['target']
        widgets = {
            'target': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['YYear'].queryset = opex_target.objects.values_list('YYear', flat=True).distinct().order_by('YYear')


class capexTargetForm(forms.ModelForm):
    class Meta:
        model = capex_target
        fields = ['target']
        widgets = {
            'target': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['YYear'].queryset = capex_target.objects.values_list('YYear', flat=True).distinct().order_by('YYear')


class commercialTargetForm(forms.ModelForm):
    class Meta:
        model = commercial_target
        fields = ['target']
        widgets = {
            'target': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['YYear'].queryset = commercial_target.objects.values_list('YYear', flat=True).distinct().order_by('YYear')
    
    
    

class DeliveryWeeklyInitiativeReportForm(forms.ModelForm):
    class Meta:
        model = delivery_weekly_Initiative_Report
        fields = ['initiative_name', 'Yearly_Planned_Value', 'Yearly_Forecast_Value', 'Yearly_Actual_value', 'functions', 'overall_status', 'actual_Lgate', 'Workstream', 'SavingType',]  # or list specific fields if you want to restrict
        # widgets = {
        #     'Planned_Date': forms.DateInput(attrs={'type': 'date'}),
        #     'L0_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L1_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L2_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L3_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L4_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L5_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        # }
        
class OpexWeeklyInitiativeReportForm(forms.ModelForm):
    class Meta:
        model = opex_weekly_Initiative_Report
        fields = ['initiative_name', 'Yearly_Planned_Value', 'Yearly_Forecast_Value', 'Yearly_Actual_value', 'functions', 'overall_status', 'actual_Lgate', 'Workstream', 'SavingType',]  # or list specific fields if you want to restrict
        # widgets = {
        #     'Planned_Date': forms.DateInput(attrs={'type': 'date'}),
        #     'L0_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L1_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L2_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L3_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L4_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        #     'L5_Completion_Date_Planned': forms.DateInput(attrs={'type': 'date'}),
        # }