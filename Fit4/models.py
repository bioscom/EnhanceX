from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
#from ckeditor5.fields import CKEditor5Field
from django.utils.text import slugify


import base64
import os
from uuid import uuid4

class BaseModel(models.Model):
    Created_Date  = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    last_modified_date = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True # This makes the model abstract

# Source: https://forum.djangoproject.com/t/django-auto-sequence-number-with-alpha-numeric-key-uniuqe-with-orm/30666
# This model is very important to hold the numbers of records that can be generated into the database. {:08d}, can generate 100 million records
# Increase to {:010d} in the future, which has capacity to generate 100 billion records. 
class ControlSequence(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sequence_number = models.IntegerField(default=0)
    prefix = models.CharField(max_length=10)

    @classmethod
    def get_next_number(cls, sequence_name):
        with transaction.atomic():
            sequence = cls.objects.select_for_update().get(name=sequence_name)
            sequence.sequence_number += 1
            sequence.save()
            return sequence.prefix + '-' + ("{:08d}".format(sequence.sequence_number))
        
class Banner(models.Model):
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='banners/')
    is_active = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title or f"Banner {self.id}"

class Formula_Level_1(BaseModel):
    name = models.CharField(_('name'), max_length=250)

    def __str__(self):
        return self.name

class Formula_Level_2(BaseModel):
    name = models.CharField(_('name'), max_length=250)
    formula_Level_1 = models.ForeignKey(Formula_Level_1, related_name='formula_Formula1', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

class Formula_Level_3(BaseModel):
    name = models.CharField(_('name'), max_length=250)
    formula_Level_2 = models.ForeignKey(Formula_Level_2, related_name='formula_Formula2', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

class Formula_Level_4(BaseModel):
    name = models.CharField(_('name'), max_length=250)
    formula_Level_3 = models.ForeignKey(Formula_Level_3, related_name='formula_Formula3', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

class Functions(BaseModel):
    title = models.CharField(_('title'), max_length=150)
    
    def __str__(self):
        return self.title

class Currency(BaseModel):
    title = models.CharField(_('title'), max_length=150)
    
    def __str__(self):
        return self.title
    
class Frequency(BaseModel):
    title = models.CharField(_('title'), max_length=150)
    
    def __str__(self):
        return self.title
    
class SavingsType(BaseModel):
    title = models.CharField(_('title'), max_length=150)
    
    def __str__(self):
        return self.title
    
class PlanRelevance(BaseModel):
    title = models.CharField(_('title'), max_length=150)
    
    def __str__(self):
        return self.title

class Workstream(BaseModel):
    workstreamname = models.CharField(max_length=250)
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rel_workstream_owner')
    user_workstreamsponsor = models.ForeignKey(User, related_name='workstream_sponsor', on_delete=models.CASCADE)
    user_workstreamlead = models.ForeignKey(User, related_name='workstream_wslead', on_delete=models.CASCADE)
    user_financesponsor = models.ForeignKey(User, related_name='workstream_finance', on_delete=models.CASCADE)
    
    workstreamtarget = models.DecimalField(max_digits = 20, decimal_places = 2, blank=True,null=True)
    workstreamambition = models.DecimalField(max_digits = 20, decimal_places = 2, blank=True,null=True)
    workstreamdescription = RichTextUploadingField(blank=True,null=True, config_name='default')

    #<! -- Asset Heirarchy -->
    formula_Level_1 = models.ForeignKey(Formula_Level_1, related_name='workstream_Formula1', on_delete=models.CASCADE, blank=True, null=True)
    formula_Level_2 = models.ForeignKey(Formula_Level_2, related_name='workstream_Formula2', on_delete=models.CASCADE, blank=True, null=True)
    formula_Level_3 = models.ForeignKey(Formula_Level_3, related_name='workstream_Formula3', on_delete=models.CASCADE, blank=True, null=True)
    formula_Level_4 = models.ForeignKey(Formula_Level_4, related_name='workstream_Formula4', on_delete=models.CASCADE, blank=True, null=True)
    functions = models.ForeignKey(Functions,  on_delete=models.CASCADE, blank=True, null=True, related_name='workstream_Function')
    SavingType = models.ForeignKey(SavingsType,  on_delete=models.CASCADE, blank=True, null=True, related_name='workstream_SavingsType')

    slug = models.SlugField(_('slug'), max_length=130, blank=True)
    
    created_by = models.ForeignKey(User, related_name='rel_created_set', on_delete=models.CASCADE)
    last_modified_by = models.ForeignKey(User, related_name='rel_modified_set', on_delete=models.CASCADE)

    class Meta:
        ordering = ('workstreamname',)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.workstreamname)
        super().save(*args, **kwargs)
    
    def is_mto(self):
        return 'mto' in self.workstreamname.lower()
    
    def __str__(self):
        return self.workstreamname
    

class EnabledBy(BaseModel):
    enabledby = models.CharField(max_length=200)
    
    def __str__(self):
        return self.enabledby

class Actual_L_Gate(BaseModel):
    LGate = models.CharField(max_length=35, blank=True, null=True)
    GateIndex = models.IntegerField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='rel_created_Lgate', blank=True,null=True, on_delete=models.CASCADE)
    last_modified_by = models.ForeignKey(User, related_name='rel_modified_Lgate', blank=True,null=True, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.LGate
    
class PredefinedApprovers(BaseModel):
    Workstream = models.ForeignKey(Workstream, related_name='PredefinedApprovers_workstream', on_delete=models.CASCADE)
    actual_Lgate = models.ForeignKey(Actual_L_Gate, related_name='PredefinedApprovers_Actual_LGate', on_delete=models.CASCADE)

    workstreamsponsor = models.ForeignKey(User, related_name='PredefinedApprovers_sponsor', blank=True,null=True, on_delete=models.CASCADE)
    workstreamsponsor2 = models.ForeignKey(User, related_name='PredefinedApprovers_sponsor2', blank=True,null=True, on_delete=models.CASCADE)
    workstreamsponsor3 = models.ForeignKey(User, related_name='PredefinedApprovers_sponsor3', blank=True,null=True, on_delete=models.CASCADE)

    workstreamlead = models.ForeignKey(User, related_name='PredefinedApprovers_wslead', blank=True,null=True, on_delete=models.CASCADE)
    workstreamlead2 = models.ForeignKey(User, related_name='PredefinedApprovers_wslead2', blank=True,null=True, on_delete=models.CASCADE)
    workstreamlead3 = models.ForeignKey(User, related_name='PredefinedApprovers_wslead3', blank=True,null=True, on_delete=models.CASCADE)

    financesponsor = models.ForeignKey(User, related_name='PredefinedApprovers_finance', blank=True,null=True, on_delete=models.CASCADE)
    financesponsor2 = models.ForeignKey(User, related_name='PredefinedApprovers_finance2', blank=True,null=True, on_delete=models.CASCADE)
    financesponsor3 = models.ForeignKey(User, related_name='PredefinedApprovers_finance3', blank=True,null=True, on_delete=models.CASCADE)

    created_by = models.ForeignKey(User, related_name='rel_created_PredefinedApprovers', on_delete=models.CASCADE)
    last_modified_by = models.ForeignKey(User, related_name='rel_modified_PredefinedApprovers', blank=True,null=True, on_delete=models.CASCADE)

    
class Discipline(BaseModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.title

class approvalStatusVisual(BaseModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.title

class overall_status(BaseModel):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class record_type(BaseModel):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class InfrastructureCategory(BaseModel):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class Threshold(BaseModel):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

#region ======================= MTO Models Phase 1 =========================================

class Unit(BaseModel):
    name = models.CharField(max_length=100)
    rated_capacity = models.IntegerField(blank=True, null=True)
    UOM = models.CharField(max_length=2000, blank=True, null=True)
    margin = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    impactDays = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    days = models.IntegerField(blank=True, null=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='unit_created_by')
    last_modified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='unit_modified_by')
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class ProactiveType(BaseModel):
    name = models.CharField(max_length=300)
    def __str__(self):
        return self.name

#Likelihood of Asset Consequencies
class Severity(BaseModel):
    factor = models.IntegerField(blank=True, null=True)
    def __str__(self):
        return self.factor
    
class AssetConsequence(BaseModel):
    name = models.CharField(max_length=300)
    def __str__(self):
        return self.name
    
class PeopleConsequences(BaseModel):
    name = models.CharField(max_length=300)
    def __str__(self):
        return self.name

class CommunityConsequences(BaseModel):
    name = models.CharField(max_length=300)
    def __str__(self):
        return self.name
    
class EnvironmentalConsequences(BaseModel):
    name = models.CharField(max_length=300)
    def __str__(self):
        return self.name

class ThreatLikelihood(BaseModel):
    name = models.CharField(max_length=300)
    factor = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    RAM = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return self.name

class RamBox(BaseModel):
    name = models.CharField(max_length=300)
    def __str__(self):
        return self.name
 
class RamColor(BaseModel):
    name = models.CharField(max_length=300)
    def __str__(self):
        return self.name

class ImpactCategory(BaseModel):
    name = models.CharField(max_length=300)
    def __str__(self):
        return self.name

#endregion ================================================================

    
class Initiative(BaseModel):
    #<------ Required Fields ----->
    initiative_id = models.CharField(max_length=15)
    oldinitiative_id = models.CharField(max_length=15, blank=True, null=True)
    initiative_name = models.CharField(_('initiative name'), max_length=80)

    #<! -- Asset Heirarchy -->
    formula_Level_1 = models.ForeignKey(Formula_Level_1, related_name='initiative_Formula1', on_delete=models.CASCADE, blank=True, null=True)
    formula_Level_2 = models.ForeignKey(Formula_Level_2, related_name='initiative_Formula2', on_delete=models.CASCADE, blank=True, null=True)
    formula_Level_3 = models.ForeignKey(Formula_Level_3, related_name='initiative_Formula3', on_delete=models.CASCADE, blank=True, null=True)
    formula_Level_4 = models.ForeignKey(Formula_Level_4, related_name='initiative_Formula4', on_delete=models.CASCADE, blank=True, null=True)
    functions = models.ForeignKey(Functions,  on_delete=models.CASCADE, blank=True, null=True, related_name='initiative_Function')
    SavingType = models.ForeignKey(SavingsType,  on_delete=models.CASCADE, blank=True, null=True, related_name='initiative_SavingsType')
    threshold = models.ForeignKey(Threshold,  on_delete=models.CASCADE, blank=True, null=True, related_name='initiative_Threshold')
    
    Workstream = models.ForeignKey(Workstream, related_name='initiative_workstream', on_delete=models.CASCADE)
    actual_Lgate = models.ForeignKey(Actual_L_Gate, related_name='initiative_Actual_LGate', on_delete=models.CASCADE, default = '1')
    overall_status = models.ForeignKey(overall_status, related_name='initiative_overall_status', on_delete=models.CASCADE, default = '1')
    recordType = models.ForeignKey(record_type, related_name='initiative_recordType', on_delete=models.CASCADE, blank=True, null=True)
    infrastructureCategory = models.ForeignKey(InfrastructureCategory, related_name='initiative_Threat_Category', on_delete=models.CASCADE, blank=True, null=True)
    
    currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.CASCADE, related_name='initiative_impact_currency')
    slug = models.SlugField(_('slug'), unique=True, max_length=255, blank=True)
    #slug = models.AutoSlugField(populate_from='initiative_name', unique=True, max_length=130, blank=True)
    
    approval_status_visual = models.ForeignKey(approvalStatusVisual, on_delete=models.CASCADE, blank=True, null=True, related_name='initiative_approvalStatus') 
    next_Lgate_Comment = models.TextField(null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiative_owner')
    
    #<---- End Required Fields ------>
    
    description = RichTextUploadingField(null=True, blank=True, config_name='default') 
    problem_statement = RichTextUploadingField(null=True, blank=True, config_name='default') 
    overallstatuscommentary = RichTextUploadingField(null=True, blank=True, config_name='default')
    discipline = models.ForeignKey(Discipline,  on_delete=models.CASCADE, blank=True, null=True, related_name='initiative_Discipline')

    workstreamsponsor = models.ForeignKey(User, related_name='initiative_wssponsor', blank=True, null=True, on_delete=models.CASCADE)
    workstreamlead = models.ForeignKey(User, related_name='initiative_wslead', blank=True, null=True, on_delete=models.CASCADE)
    financesponsor = models.ForeignKey(User, related_name='initiative_finance', blank=True, null=True, on_delete=models.CASCADE)
    initiativesponsor = models.ForeignKey(User, related_name='initiative_sponsor', blank=True, null=True, on_delete=models.CASCADE)
    
    Yearly_Planned_Value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Yearly_Forecast_Value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Yearly_Actual_value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    
    enabledby = models.ManyToManyField(EnabledBy, blank=True, related_name='initiative_enabledby')
    Plan_Relevance = models.ManyToManyField(PlanRelevance, blank=True, related_name='initiative_planrelevance')
    
    L0_Completion_Date_Planned = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L1_Completion_Date_Planned = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L2_Completion_Date_Planned = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L3_Completion_Date_Planned = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L4_Completion_Date_Planned = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L5_Completion_Date_Planned = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    
    L0_Completion_Date_Actual = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L1_Completion_Date_Actual = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L2_Completion_Date_Actual = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L3_Completion_Date_Actual = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L4_Completion_Date_Actual = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    L5_Completion_Date_Actual = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    
    Planned_Date = models.DateField(auto_now_add=False, blank=True, null=True, db_index=True)
    Approval_Status  = models.CharField(max_length=255, blank=True, null=True)
    HashTag =  models.TextField(null=True, blank=True) 
    
    mark_as_confidential = models.BooleanField(default=False)
    activate_initiative_approvers = models.BooleanField(default=False)

    is_carbon_abatement_opportunity = models.BooleanField(default=False)
    can_be_replicated = models.BooleanField(default=False)
    is_this_a_replicated_initiative = models.BooleanField(default=False)
    rationale_for_replication = models.TextField(null=True, blank=True)
    description_of_solution_identified = models.TextField(null=True, blank=True)
    learning_and_description_of_work_done = models.TextField(null=True, blank=True)

    #region ==================== MTO Related data =================================
    unit = models.ForeignKey(Unit, related_name='initiative_Unit', on_delete=models.CASCADE, blank=True, null=True)
    calculated_asset_consequences = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    asset_consequences = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    mto_score = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    asset_consequence = models.ForeignKey(AssetConsequence, related_name='initiative_AssetConsequence', on_delete=models.CASCADE, blank=True, null=True)
    likelihood_asset_consequence = models.ForeignKey(ThreatLikelihood, related_name='asset_ThreatLikelihood', on_delete=models.CASCADE, blank=True, null=True)
    people_consequence = models.ForeignKey(PeopleConsequences, related_name='initiative_PeopleConsequences', on_delete=models.CASCADE, blank=True, null=True)
    likelihood_people_consequence = models.ForeignKey(ThreatLikelihood, related_name='people_ThreatLikelihood', on_delete=models.CASCADE, blank=True, null=True)
    community_consequence = models.ForeignKey(CommunityConsequences, related_name='initiative_CommunityConsequences', on_delete=models.CASCADE, blank=True, null=True)
    likelihood_community_consequence = models.ForeignKey(ThreatLikelihood, related_name='community_ThreatLikelihood', on_delete=models.CASCADE, blank=True, null=True)
    environmental_consequence = models.ForeignKey(EnvironmentalConsequences, related_name='initiative_EnvironmentalConsequences', on_delete=models.CASCADE, blank=True, null=True)
    likelihood_environment_consequence = models.ForeignKey(ThreatLikelihood, related_name='environment_ThreatLikelihood', on_delete=models.CASCADE, blank=True, null=True)
    primary_ram_box = models.ForeignKey(RamBox, related_name='primary_rambox', on_delete=models.CASCADE, blank=True, null=True)
    primary_ram_color = models.ForeignKey(RamBox, related_name='primary_ramcolor', on_delete=models.CASCADE, blank=True, null=True)
    second_ram_box = models.ForeignKey(RamBox, related_name='secondary_ramBox', on_delete=models.CASCADE, blank=True, null=True)
    second_ram_color = models.ForeignKey(RamColor, related_name='secondary_ramcolor', on_delete=models.CASCADE, blank=True, null=True)
    highest_impact_category = models.ForeignKey(ImpactCategory, related_name='highest_ImpactCategory', on_delete=models.CASCADE, blank=True, null=True)
    second_highest_impact_category = models.ForeignKey(ImpactCategory, related_name='second_ImpactCategory', on_delete=models.CASCADE, blank=True, null=True)

    #severityJustification = RichTextUploadingField(blank=True, null=True, config_name='default')
    #likehoodJustification = RichTextUploadingField(blank=True, null=True, config_name='default')

    impact_justification = RichTextUploadingField(blank=True, null=True, config_name='default')
    likelihood_justification = RichTextUploadingField(blank=True, null=True, config_name='default')
    proactive_type = models.ForeignKey(ProactiveType, related_name='initiative_ProactiveType', on_delete=models.CASCADE, blank=True, null=True)
    PotentialProductionCost=models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    PotentialNonProductionCost=models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)

    #endregion=====================================================================

    DocumentLink = models.CharField(max_length=2000, blank=True, null=True)
    SharepointUrl = models.CharField(max_length=2000, blank=True, null=True)
    
    YYear = models.CharField(max_length=4, blank=True, null=True)

    note = models.CharField(max_length=255, blank=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='created_by')
    last_modified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='modified_by')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ('-initiative_id',)
        
    # def save(self, *args, **kwargs):
    #     if not self.slug:
    #         self.slug = slugify(self.initiative_name)
    #     super().save(*args, **kwargs)
    
    def __str__(self):
        return self.initiative_name
    
    
    def get_absolute_url(self):
        return reverse('Fit4:initiative_details', args=[self.initiative_id])
    
    
    @property
    def InitiativeOwnerFullName(self):
        return str('' if self.author.first_name is None else self.author.first_name)  + ', ' + str('' if self.author.last_name is None else self.author.last_name)
        #return self.author.first_name + ', ' + self.author.last_name
    
    @property
    def InitiativeSponsorFullName(self):
        return str('' if self.initiativesponsor.first_name is None else self.initiativesponsor.first_name)  + ', ' + str('' if self.initiativesponsor.last_name is None else self.initiativesponsor.last_name)
        #return self.initiativesponsor.first_name + ', ' + self.initiativesponsor.last_name

    @property
    def WorstreamSponsorFullName(self):
        return str('' if self.workstreamsponsor.first_name == None else self.workstreamsponsor.first_name)  + ', ' + str('' if self.workstreamsponsor.last_name == None else self.workstreamsponsor.last_name)
        #return self.workstreamsponsor.first_name + ', ' + self.workstreamsponsor.last_name

    @property
    def WorkstreamLeadFullName(self):
        return str('' if self.workstreamlead.first_name is None else self.workstreamlead.first_name)  + ', ' + str('' if self.workstreamlead.last_name is None else self.workstreamlead.last_name)
        #return self.workstreamlead.first_name + ', ' + self.workstreamlead.last_name

    @property
    def FinanceSponsorFullName(self):
        return str('' if self.financesponsor.first_name is None else self.financesponsor.first_name)  + ', ' + str('' if self.financesponsor.last_name is None else self.financesponsor.last_name)
        #return self.financesponsor.first_name + ', ' + self.financesponsor.last_name
    
class InitiativeApprovals(BaseModel):
    #<------ Required Fields ----->
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_approvals')
    LGateId = models.ForeignKey(Actual_L_Gate, blank=True, null=True, on_delete=models.CASCADE, related_name='initiative_approvals_LGate')
    comments = models.TextField(null=True, blank=True) 
    approver = models.ForeignKey('auth.User', related_name='initiative_approved_by', blank=True, null=True, on_delete=models.CASCADE)
    actualApprover = models.ForeignKey('auth.User', related_name='actualAprover_approved_by', blank=True, null=True, on_delete=models.CASCADE)
    status = models.IntegerField(blank=True, null=True)
    rolePlayed = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='approval_created_by')
    last_modified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='approval_modified_by')
    
    #Created_Date  = models.DateTimeField(auto_now_add=True, blank=True, null=True, db_index=True)
    #updated = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    def __str__(self):
        return self.initiative
    
    class Meta:
        ordering=['-Created_Date']

class BenefitType(BaseModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.title

def get_years():
    date_range = 7 
    this_year = datetime.now().year
    return {i: i for i in range(this_year - date_range, this_year + date_range)}

class InitiativeImpact(BaseModel):
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_initiative_impact')
    benefittype = models.ForeignKey(BenefitType, blank=True, null=True, on_delete=models.CASCADE, related_name='initiative_benefittype')
    frequency = models.ForeignKey(Frequency, blank=True, null=True, on_delete=models.CASCADE, related_name='initiative_frequency')
    
    YYear = models.IntegerField(blank=True, null=True, choices=get_years(), default=datetime.now().year)
    
    Jan_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Feb_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Mar_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Apr_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    May_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Jun_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Jul_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Aug_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Sep_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Oct_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Nov_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Dec_Plan = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    
    Jan_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Feb_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Mar_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Apr_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    May_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Jun_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Jul_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Aug_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Sep_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Oct_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Nov_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Dec_Forecast = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    
    Jan_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Feb_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Mar_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Apr_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    May_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Jun_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Jul_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Aug_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Sep_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Oct_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Nov_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    Dec_Actual = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)

    raecShare = models.CharField(max_length=100, null=True, blank=True, default='100%')
    impactBusinessResult = models.BooleanField(max_length=100, null=True, blank=True, default=False)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='impact_created_by')
    last_modified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='impact_modified_by')

    @property
    def sum_plan(self):
        return float(0 if self.Jan_Plan is None else self.Jan_Plan) + float(0 if self.Feb_Plan is None else self.Feb_Plan) + float(0 if self.Mar_Plan is None else self.Mar_Plan) + float(0 if self.Apr_Plan is None else self.Apr_Plan) + float(0 if self.May_Plan is None else self.May_Plan) + float(0 if self.Jun_Plan is None else self.Jun_Plan) + float(0 if self.Jul_Plan is None else self.Jul_Plan) + float(0 if self.Aug_Plan is None else self.Aug_Plan) + float(0 if self.Sep_Plan is None else self.Sep_Plan) + float(0 if self.Oct_Plan is None else self.Oct_Plan) + float(0 if self.Nov_Plan is None else self.Nov_Plan) + float(0 if self.Dec_Plan is None else self.Dec_Plan)

    @property
    def sum_forecast(self):
        return float(0 if self.Jan_Forecast is None else self.Jan_Forecast) + float(0 if self.Feb_Forecast is None else self.Feb_Forecast) + float(0 if self.Mar_Forecast is None else self.Mar_Forecast) + float(0 if self.Apr_Forecast is None else self.Apr_Forecast) + float(0 if self.May_Forecast is None else self.May_Forecast) + float(0 if self.Jun_Forecast is None else self.Jun_Forecast) + float(0 if self.Jul_Forecast is None else self.Jul_Forecast) + float(0 if self.Aug_Forecast is None else self.Aug_Forecast) + float(0 if self.Sep_Forecast is None else self.Sep_Forecast) + float(0 if self.Oct_Forecast is None else self.Oct_Forecast) + float(0 if self.Nov_Forecast is None else self.Nov_Forecast) + float(0 if self.Dec_Forecast is None else self.Dec_Forecast)
    
    @property
    def sum_actual(self):
        return float(0 if self.Jan_Actual is None else self.Jan_Actual) + float(0 if self.Feb_Actual is None else self.Feb_Actual) + float(0 if self.Mar_Actual is None else self.Mar_Actual) + float(0 if self.Apr_Actual is None else self.Apr_Actual) + float(0 if self.May_Actual is None else self.May_Actual) + float(0 if self.Jun_Actual is None else self.Jun_Actual) + float(0 if self.Jul_Actual is None else self.Jul_Actual) + float(0 if self.Aug_Actual is None else self.Aug_Actual) + float(0 if self.Sep_Actual is None else self.Sep_Actual) + float(0 if self.Oct_Actual is None else self.Oct_Actual) + float(0 if self.Nov_Actual is None else self.Nov_Actual) + float(0 if self.Dec_Actual is None else self.Dec_Actual)
    
    # def __str__(self):
    #     return self.benefittype
    
class TeamMembers(BaseModel):
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_teammember')
    member = models.ForeignKey(User, related_name='member_teammember', blank=True, null=True, on_delete=models.CASCADE)
    resourcetimeallocation = models.CharField(max_length=200, blank=True, null=True)
    discipline = models.CharField(max_length=200, blank=True, null=True)
    
    created_by = models.ForeignKey('auth.User', related_name='member_created_by', on_delete=models.CASCADE, blank=True, null=True)
    last_modified_by = models.ForeignKey('auth.User', related_name='member_modified_by', on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return self.member
    
class action_status(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class action_type(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Actions(BaseModel):
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_actions')
    action_name = models.CharField(_('action name'), max_length=80)
    action_type = models.ForeignKey(action_type, blank=True, null=True,  on_delete=models.CASCADE)
    complete_by_phase = models.ForeignKey(Actual_L_Gate, related_name='action_lgate', blank=True, null=True, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    commentary = models.TextField(null=True, blank=True)
    start_date = models.DateTimeField(auto_now_add=False, blank=True, null=True, db_index=True)
    due_date = models.DateTimeField(auto_now_add=False, blank=True, null=True, db_index=True)
    completion_date = models.DateTimeField(auto_now_add=False, blank=True, null=True, db_index=True)
    assigned_to = models.ForeignKey(User, related_name='action_assignedto', blank=True, null=True, on_delete=models.CASCADE)
    status = models.ForeignKey(action_status, blank=True, null=True, on_delete=models.CASCADE) 

    send_email = models.BooleanField(default=True)
    
    created_by = models.ForeignKey('auth.User', related_name='action_created_by', on_delete=models.CASCADE)
    last_modified_by = models.ForeignKey('auth.User', related_name='action_modified_by', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.description

def initiative_upload_path(instance, filename):
    return os.path.join(f'initiatives/{instance.initiative.initiative_id}', filename)
    
class InitiativeFiles(BaseModel):
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_file')
    initiativeFiles = models.FileField(upload_to=initiative_upload_path, blank=True, null=True, max_length=256)
    
    created_by = models.ForeignKey('auth.User', related_name='file_created_by', on_delete=models.CASCADE, blank=True, null=True)
    last_modified_by = models.ForeignKey('auth.User', related_name='file_modified_by', on_delete=models.CASCADE, blank=True, null=True)
    
    def extension(self):
        name, extension = os.path.splitext(self.initiativeFiles.name)
        return extension
    
    def filesize(self):
        #Returns the filesize of the filename given in value"""
        file_size_kb = os.path.getsize(self.initiativeFiles.path) / 1024
        return f"{file_size_kb:.2f} Kb"

class InitiativeNotes(BaseModel):
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_note')
    title = models.CharField(_('title'), blank=True, null=True, max_length=100)
    Notes = RichTextUploadingField(blank=True, null=True, config_name='default')
    
    created_by = models.ForeignKey('auth.User', related_name='note_created_by', on_delete=models.CASCADE, blank=True, null=True)
    last_modified_by = models.ForeignKey('auth.User', related_name='note_modified_by', on_delete=models.CASCADE, blank=True, null=True)


class MenuItem(BaseModel):
    name = models.CharField(max_length=100)
    url = models.URLField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True) # optional for UI
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey('auth.User', related_name='menu_created_by', on_delete=models.CASCADE, blank=True, null=True)
    last_modified_by = models.ForeignKey('auth.User', related_name='menu_modified_by', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

class UserMenuConfig(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    is_visible = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'menu_item')

class FCFMultiplier(BaseModel):
    name = models.CharField(max_length=100)
    benefittype = models.ForeignKey(BenefitType, blank=True, null=True, on_delete=models.CASCADE, related_name='fcfmultiplier_benefittype')
    actual_volume_multiplier = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    forecast_volume_multiplier = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    planned_volume_multiplier = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    fcf_multiplier = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)
    YYear = models.IntegerField(blank=True, null=True, choices=get_years, default = datetime.now().year)
    


#region ================== MTO Models Phase 2 ===========================================

class UnitImpactEntry(BaseModel):       #=====MTO Impact Calculator=============
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_units')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    percent_impact = models.FloatField(null=True, blank=True)
    days = models.FloatField(null=True, blank=True)
    impact_day = models.FloatField(null=True, blank=True)
    financial_impact = models.FloatField(null=True, blank=True)

class MTOScore(models.Model):           #=======MTO Scores =========
    cell_index = models.IntegerField()
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_mtoscore')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='unit_mtoscore')

    class Meta:
        unique_together = ('cell_index', 'unit', 'initiative')

    def __str__(self):
        return f"Cell {self.cell_index} - PU: {self.production_unit} - IN: {self.initiative}"
        #return f"Initiative: {self.initiative.initiative_name} | Unit: {self.unit.name} | Cell {self.cell_index}: {', '.join(self.value)}"

class SelectionValue(models.Model):
    MTOScore_selection = models.ForeignKey(MTOScore, related_name='values', on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.value
      
#endregion ============================================================================

class Paginating(models.Model):
    number_of_pages = models.IntegerField(default=0)

#region========================== Likely No longer useful =============================
class MTOScoring(BaseModel):
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_MTO')
    A0 = models.CharField(max_length=100, blank=True, null=True)
    B0 = models.CharField(max_length=100, blank=True, null=True)
    C0 = models.CharField(max_length=100, blank=True, null=True)
    D0 = models.CharField(max_length=100, blank=True, null=True)
    E0 = models.CharField(max_length=100, blank=True, null=True)

    A1 = models.CharField(max_length=100, blank=True, null=True)
    B1 = models.CharField(max_length=100, blank=True, null=True)
    C1 = models.CharField(max_length=100, blank=True, null=True)
    D1 = models.CharField(max_length=100, blank=True, null=True)
    E1 = models.CharField(max_length=100, blank=True, null=True)

    A2 = models.CharField(max_length=100, blank=True, null=True)
    B2 = models.CharField(max_length=100, blank=True, null=True)
    C2 = models.CharField(max_length=100, blank=True, null=True)
    D2 = models.CharField(max_length=100, blank=True, null=True)
    E2 = models.CharField(max_length=100, blank=True, null=True)

    A3 = models.CharField(max_length=100, blank=True, null=True)
    B3 = models.CharField(max_length=100, blank=True, null=True)
    C3 = models.CharField(max_length=100, blank=True, null=True)
    D3 = models.CharField(max_length=100, blank=True, null=True)
    E3 = models.CharField(max_length=100, blank=True, null=True)

    A4 = models.CharField(max_length=100, blank=True, null=True)
    B4 = models.CharField(max_length=100, blank=True, null=True)
    C4 = models.CharField(max_length=100, blank=True, null=True)
    D4 = models.CharField(max_length=100, blank=True, null=True)
    E4 = models.CharField(max_length=100, blank=True, null=True)

    A5 = models.CharField(max_length=100, blank=True, null=True)
    B5 = models.CharField(max_length=100, blank=True, null=True)
    C5 = models.CharField(max_length=100, blank=True, null=True)
    D5 = models.CharField(max_length=100, blank=True, null=True)
    E5 = models.CharField(max_length=100, blank=True, null=True)

    created_by = models.ForeignKey('auth.User', related_name='MTO_created_by', on_delete=models.CASCADE, blank=True, null=True)
    last_modified_by = models.ForeignKey('auth.User', related_name='MTO_modified_by', on_delete=models.CASCADE, blank=True, null=True)

    # def __str__(self):
    #     return self.A0
    
class MTOScoringInfo(BaseModel):
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='initiative_MTOScoring')
    proactive = models.ForeignKey(ProactiveType, on_delete=models.CASCADE, related_name='scoring_proactive')
    #assetConsequence = models.ForeignKey(AssetConsequence, on_delete=models.CASCADE, blank=True, null=True, related_name='asset_consequence')
    proactiveType = models.BooleanField(default=False)
    likelyhoodAssetConsequence = models.BooleanField(default=False)
    severityJustification = RichTextUploadingField(blank=True, null=True, config_name='default')
    likehoodJustification = RichTextUploadingField(blank=True, null=True, config_name='default')
    mtoScore = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) 

#endregion ============================================================================

    
# === Codes to migrate models into database === #
# python manage.py makemigrations
# python manage.py migrate

# === command to activate virtual environment
# .venv\scripts\activate 

# === gitHub commands to push codes to the gitHub from the command line
# git remote add origin https://github.com/bioscom/Renaissance.git
# git branch -M main
# git push -u origin main

# git push -f origin main   --useful one now