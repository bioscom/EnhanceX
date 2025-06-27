from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from Fit4.models import *
# Create your models here.


class report_category(models.Model):
    category = models.CharField(_('category'), max_length=150)
    
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    created_by = models.ForeignKey(User, related_name='category_created_set', blank=True, null=True, on_delete=models.CASCADE)
    last_modified_by = models.ForeignKey(User, related_name='category_modified_set', blank=True, null=True, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.category
    
class SavedFilter(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(report_category, on_delete=models.CASCADE, related_name='SavedFilter_category')
    unique_name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    filter_params = models.TextField(null=True, blank=True)
    filter_params2 = models.JSONField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        ordering = ('-date_created',)
    
    def __str__(self):
        return self.name


class report(models.Model):
    name = models.CharField(_('report name'), max_length=120)
    category = models.ForeignKey(report_category, on_delete=models.CASCADE, related_name='report_category')
    unique_name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    
    WorkStream = models.TextField(null=True, blank=True)
    wsFilters = models.TextField(null=True, blank=True)
    
    overall_status = models.TextField(null=True, blank=True)
    osFilters = models.TextField(null=True, blank=True)
    
    discipline = models.TextField(blank=True, null=True)
    discFilters = models.TextField(null=True, blank=True)
    Function = models.TextField(blank=True, null=True)
    funcFilters = models.TextField(null=True, blank=True)
    SavingType = models.TextField(blank=True, null=True)
    stFilters = models.TextField(null=True, blank=True)
    
    Plan_Relevance = models.TextField(null=True, blank=True)
    psFilters = models.TextField(null=True, blank=True)
    
    HashTag =  models.TextField(null=True, blank=True)
    htFilters = models.TextField(null=True, blank=True)
    
    workStreamSponsor = models.TextField(blank=True, null=True)
    workStreamLead = models.TextField(blank=True, null=True)
    financeSponsor = models.TextField(blank=True, null=True)
    initiativeSponsor = models.TextField(blank=True, null=True)
    initiativeOwner = models.TextField(blank=True, null=True)
    
    updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    YYear = models.CharField(max_length=255, blank=True, null=True)
    yearFilter = models.TextField(null=True, blank=True)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(User, related_name='report_created_set', on_delete=models.CASCADE)
    last_modified_by = models.ForeignKey('auth.User', related_name='report_modified_set', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ('-name',)
    
    def __str__(self):
        return self.name
    
# class Report_Filter_parameters(models.Model):
#     filter_name = models.CharField(max_length=100)
#     filter_lookup = models.CharField(max_length=100, null=True, blank=True)
    
#     class Meta:
#         ordering = ('-filter_name',)

# class initiative_report_filter(models.Model):
#     iReport = models.ForeignKey(report, on_delete=models.CASCADE, related_name='initiative_report_header')
#     WorkStreamName = models.TextField(null=True, blank=True)
#     # actual_LGate = models.ForeignKey(Actual_L_Gate, related_name='initiative_report_Actual_LGate', on_delete=models.CASCADE)
    
#     overall_status = models.TextField(null=True, blank=True)
    
#     author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='initiative_report_owner')
#     #<---- End Required Fields ------>
    
#     discipline = models.TextField(blank=True, null=True)
#     Function = models.TextField(blank=True, null=True)
#     SavingType = models.TextField(blank=True, null=True)
#     workStreamSponsor = models.TextField(blank=True, null=True)
#     workStreamLead = models.TextField(blank=True, null=True)
#     financeSponsor = models.TextField(blank=True, null=True)
#     initiativeSponsor = models.TextField(blank=True, null=True)
    
#     Plan_Relevance = models.TextField(null=True, blank=True)
    
#     Approval_Status  = models.CharField(max_length=255, blank=True, null=True)
#     HashTag =  models.TextField(null=True, blank=True) 
#     Created_Date  = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
#     updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#     YYear = models.IntegerField(blank=True, null=True)

# class report_header(models.Model):
#     columnsNames = models.CharField(max_length=120)
#     reporting = models.ForeignKey(report, on_delete=models.CASCADE, related_name='report_header')
    
#     date_created = models.DateTimeField(auto_now_add=True)
#     date_updated = models.DateTimeField(auto_now=True)
    
#     created_by = models.ForeignKey(User, related_name='report_header_set', on_delete=models.CASCADE)
#     last_modified_by = models.ForeignKey('auth.User', related_name='report_header_modified', on_delete=models.CASCADE)
    
#     class Meta:
#         ordering = ('-columnsNames',)
    
#     def __str__(self):
#         return self.columnsNames