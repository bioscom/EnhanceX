from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from Fit4.models import *
from reports.models import *
from ckeditor_uploader.fields import RichTextUploadingField
# Create your models here.

class BaseModel(models.Model):
    Created_Date  = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    last_modified_date = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True # This makes the model abstract

class dashboards(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    unique_name = models.CharField(max_length=250, null=True, blank=True)

    filter = models.ForeignKey(SavedFilter, related_name='SavedFilter_rel_set', blank=True, null=True, on_delete=models.CASCADE)
    #filter = models.ManyToManyField(SavedFilter, blank=True, related_name='SavedFilter_rel_set')
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(User, related_name='dashboard_rel_set', on_delete=models.CASCADE)
    last_modified_by = models.ForeignKey('auth.User', related_name='dashboard_rel_modified', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ('-date_updated',)
    
    def __str__(self):
        return self.name
    
#region ============================== Management Report ======================================================================================
    
class opex_weekly_Initiative_Report(BaseModel):
    workstreamlead = models.ForeignKey(User, related_name='report_wslead', blank=True, null=True, on_delete=models.CASCADE)
    workstreamsponsor = models.ForeignKey(User, related_name='report_wssponsor', blank=True, null=True, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_initiative_owner')
    initiative_name = models.CharField(_('initiative name'), max_length=80)
    initiative_id = models.CharField(max_length=15)
    Yearly_Planned_Value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Yearly_Forecast_Value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Yearly_Actual_value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Planned_Date = models.DateField(blank=True, null=True, db_index=True)
    functions = models.ForeignKey(Functions,  on_delete=models.CASCADE, blank=True, null=True, related_name='report_Function')
    slug = models.CharField(max_length=255, blank=True, null=True)
    
    overall_status = models.ForeignKey(overall_status, related_name='report_overall_status', on_delete=models.CASCADE)
    actual_Lgate = models.ForeignKey(Actual_L_Gate, related_name='report_Actual_LGate', on_delete=models.CASCADE)
    Plan_Relevance = models.ManyToManyField(PlanRelevance, blank=True, related_name='report_planrelevance')
    
    L0_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L1_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L2_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L3_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L4_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L5_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    Workstream = models.ForeignKey(Workstream, related_name='report_workstream', on_delete=models.CASCADE)
    SavingType = models.ForeignKey(SavingsType,  on_delete=models.CASCADE, blank=True, null=True, related_name='report_SavingsType')
    HashTag =  models.TextField(null=True, blank=True)
    Created_Date  = models.DateTimeField(blank=True, null=True, db_index=True)
    benefittype = models.ForeignKey(BenefitType, blank=True, null=True, on_delete=models.CASCADE, related_name='report_benefittype')
    Date_Downloaded  = models.DateTimeField(blank=True, null=True, db_index=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='opex_created_by')
    report_week =  models.IntegerField()
    report_year =  models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.initiative_name
    
    
class delivery_weekly_Initiative_Report(BaseModel):
    workstreamlead = models.ForeignKey(User, related_name='del_report_wslead', blank=True, null=True, on_delete=models.CASCADE)
    workstreamsponsor = models.ForeignKey(User, related_name='del_report_wssponsor', blank=True, null=True, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='del_report_initiative_owner')
    initiative_name = models.CharField(_('initiative name'), max_length=80)
    initiative_id = models.CharField(max_length=15)
    Yearly_Planned_Value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Yearly_Forecast_Value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Yearly_Actual_value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Planned_Date = models.DateField(blank=True, null=True, db_index=True)
    functions = models.ForeignKey(Functions,  on_delete=models.CASCADE, blank=True, null=True, related_name='del_report_Function')
    slug = models.CharField(max_length=255, blank=True, null=True)
    
    overall_status = models.ForeignKey(overall_status, related_name='del_report_overall_status', on_delete=models.CASCADE)
    actual_Lgate = models.ForeignKey(Actual_L_Gate, related_name='del_report_Actual_LGate', on_delete=models.CASCADE)
    Plan_Relevance = models.ManyToManyField(PlanRelevance, blank=True, related_name='del_report_planrelevance')
    
    L0_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L1_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L2_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L3_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L4_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    L5_Completion_Date_Planned = models.DateField(blank=True, null=True, db_index=True)
    Workstream = models.ForeignKey(Workstream, related_name='del_report_workstream', on_delete=models.CASCADE)
    SavingType = models.ForeignKey(SavingsType,  on_delete=models.CASCADE, blank=True, null=True, related_name='del_report_SavingsType')
    HashTag =  models.TextField(null=True, blank=True)
    Created_Date  = models.DateTimeField(blank=True, null=True, db_index=True)
    benefittype = models.ForeignKey(BenefitType, blank=True, null=True, on_delete=models.CASCADE, related_name='del_report_benefittype')
    Date_Downloaded  = models.DateTimeField(blank=True, null=True, db_index=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='del_created_by')
    report_week =  models.IntegerField()
    report_year =  models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.initiative_name

#region =========== Recognition =========================================================================================================
class delivery_weekly_recognition(BaseModel):
    recognition = RichTextUploadingField(blank=True, null=True, config_name='default')
    report_week =  models.IntegerField()
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='delivery_recognition_created_by')
    
    def __str__(self):
        return self.recognition

class opex_weekly_recognition(BaseModel):
    recognition = RichTextUploadingField(blank=True, null=True, config_name='default')
    report_week =  models.IntegerField()
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='opex_recognition_created_by')
    
    def __str__(self):
        return self.recognition
    
class capex_weekly_Recognition(BaseModel):
    recognition = RichTextUploadingField(blank=True,null=True, config_name='default')
    report_week =  models.IntegerField()
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='capex_recognition_created_by')
    #Created_Date  = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    #last_modified_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    def __str__(self):
        return self.recognition
    
class commercial_weekly_Recognition(BaseModel):
    recognition = RichTextUploadingField(blank=True,null=True, config_name='default')
    report_week =  models.IntegerField()
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='commercial_recognition_created_by')
    #Created_Date  = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    #last_modified_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    def __str__(self):
        return self.recognition
    
#endregion =================================================================================================================================


#region =========== Yearly Target =========================================================================================================
class opex_target(BaseModel):
    target = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    YYear = models.CharField(max_length=4, blank=True, null=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='opex_target_created_by')
    
    def __str__(self):
        return self.target
    
class delivery_target(BaseModel):
    target = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    YYear = models.CharField(max_length=4, blank=True, null=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='delivery_target_created_by')
    
    def __str__(self):
        return self.target
 
class capex_target(BaseModel):
    target = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    YYear = models.CharField(max_length=4, blank=True, null=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='capex_target_created_by')
    
    def __str__(self):
        return self.target   

class commercial_target(BaseModel):
    target = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    YYear = models.CharField(max_length=4, blank=True, null=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='commercial_target_created_by')
    
    def __str__(self):
        return self.target 

#endregion ====================================================================================================================================


#endregion ============================== Management Report ======================================================================================