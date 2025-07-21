from django import forms
from django.urls import reverse_lazy
from .models import *  #Profile, BlogPost, BlogPostCategories, FileUploads, Comment, ReplyComment, CommentFileUploads, Advertisement
from django.forms import ClearableFileInput, formset_factory
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm as UserCreationFormBase
from datetime import datetime
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from bootstrap_datepicker_plus.widgets import DatePickerInput

#from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from widget_tweaks.templatetags.widget_tweaks import render_field



class ExcelUploadForm(forms.Form):
    file = forms.FileField()


class CommaSeparatedNumberInput(forms.TextInput):
    def format_value(self, value):
        if isinstance(value, (int, float)):
            return "{:,}".format(value)
        return value

class ActionsForm(forms.ModelForm):
    class Meta:
        model = Actions
        fields = ('action_name', 'action_type', 'complete_by_phase', 
                'description', 'start_date', 'commentary', 'assigned_to', 
                'status', 'due_date', 'send_email')
        widgets = {
            'action_name': forms.TextInput(attrs={'placeholder': 'action_name'}),
            'start_date': DatePickerInput(options={"format": "DD/MM/YYYY"}), 
            'due_date': DatePickerInput(options={"format": "DD/MM/YYYY"}), 
        }
        labels = {
            'action_name': 'action_name',
        }
        
        
class MemberForm(forms.ModelForm):
    class Meta:
        model = TeamMembers
        fields = ('member', 'resourcetimeallocation', 'discipline',)
        

class FunctionsForm(forms.ModelForm):
    class Meta:
        model = Functions
        # fields='__all__'
        fields = ('title',)
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Function'}),
        }
        labels = {
            'title': 'Function',
        }
        
class SavingsTypeForm(forms.ModelForm):
    class Meta:
        model = SavingsType
        # fields='__all__'
        fields = ('title',)
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Savings Type'}),
        }
        labels = {
            'title': 'Savings Type',
        }
        
class BenefitTypeForm(forms.ModelForm):
    class Meta:
        model = BenefitType
        # fields='__all__'
        fields = ('title',)
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Benefit Type'}),
        }
        labels = {
            'title': 'Benefit Type',
        }
        
class PlanRelevanceForm(forms.ModelForm):
    class Meta:
        model = PlanRelevance
        # fields='__all__'
        fields = ('title',)
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Savings Type'}),
        }
        labels = {
            'title': 'Savings Type',
        }

class WorkStreamForm(forms.ModelForm):
    #workstreamdescription = forms.CharField(widget=CKEditorUploadingWidget())
    # user_workstreamsponsor=forms.ModelChoiceField(queryset=Workstream.objects.all(), required=True)
    # user_workstreamlead=forms.ModelChoiceField(queryset=Workstream.objects.all(), required=True)
    # user_financesponsor=forms.ModelChoiceField(queryset=Workstream.objects.all(), required=True)

    class Meta:
        model = Workstream
        # fields='__all__'
        fields = ('workstreamname', 'user_workstreamsponsor', 'user_workstreamlead', 
                'user_financesponsor', 'workstreamtarget', 'workstreamambition', 'workstreamdescription')
        # widgets = {
        #     'title': forms.TextInput(attrs={'placeholder': 'Savings Type'}),
        # }
        # labels = {
        #     'title': 'Savings Type',
        # }
        
class InitiativeForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = Initiative

        fields = ['initiative_name', 'Workstream', 'overall_status', 'actual_Lgate', 'description', 'mark_as_confidential']
        widgets = {
            'initiative_name': forms.TextInput(attrs={'placeholder': 'Initiative Name'}),
        }
        labels = {
            'description': 'description',
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['actual_Lgate'].queryset = Actual_L_Gate.objects.all()[:2]

class FCFMultiplierForm(forms.ModelForm):
    class Meta:
        model = FCFMultiplier

        fields = ['name', 'benefittype', 'actual_volume_multiplier', 'forecast_volume_multiplier', 'planned_volume_multiplier', 'fcf_multiplier', 'YYear']

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset', 'renaissance_share', 'capex_factor', 'opex_factor', 'oil_factor', 'domgas_factor', 'export_gas_factor']
        widgets = {
            # 'category_name': forms.TextInput(attrs={'placeholder': 'Category Name'}),
            'renaissance_share': forms.NumberInput(attrs={'placeholder': 'Renaissance Share'}),
            'capex_factor': forms.NumberInput(attrs={'placeholder': 'Capex Factor'}),
            'opex_factor': forms.NumberInput(attrs={'placeholder': 'Opex Factor'}),
            'oil_factor': forms.NumberInput(attrs={'placeholder': 'Oil Factor'}),
            'domgas_factor': forms.NumberInput(attrs={'placeholder': 'Domestic Gas Factor'}),
            'export_gas_factor': forms.NumberInput(attrs={'placeholder': 'Export Gas Factor'}),
        }

class SavingsForm(forms.ModelForm):
    class Meta:
        model = Savings
        fields = ['name']
        # widgets = {
        #     'name': forms.TextInput(attrs={'placeholder': 'Savings Name'}),
        # }
        
class ProductionFCFForm(forms.ModelForm):
    class Meta:
        model = ProductionFCF
        fields = ['name']
        # widgets = {
        #     'name': forms.TextInput(attrs={'placeholder': 'Production FCF Name'}),
        # }

class InitiativeThreatForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = Initiative

        fields = ('initiative_name', 'Workstream', 'overall_status', 'actual_Lgate', 'description', 'mark_as_confidential', 'unit', 'infrastructureCategory')
        widgets = {
            'initiative_name': forms.TextInput(attrs={'placeholder': 'Initiative Name'}),
        }
        # labels = {
        #     'description': 'description',
        # }
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['actual_Lgate'].queryset = Actual_L_Gate.objects.all()[:2]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.filter(active=True).order_by('name') # Force required in form

        
class InitiativesByWorkstreamForm(forms.ModelForm):
    class Meta:
        model = Initiative

        fields = ('id', 'initiative_name',)
        widgets = {
            'initiative_name': forms.TextInput(attrs={'placeholder': 'Initiative Name'}),
        }
        labels = {
            #'description': 'description',
        }

class AssetHierarchyForm(forms.ModelForm):
    class Meta:
        model = Initiative
        fields = ['formula_Level_1', 'formula_Level_2', 'formula_Level_3', 'formula_Level_4', 'functions', 'SavingType', ]
        
        widgets = {
            'formula_Level_1': forms.Select(attrs={'class': 'form-select'}),
            'formula_Level_2': forms.Select(attrs={'class': 'form-select'}),
            'formula_Level_3': forms.Select(attrs={'class': 'form-select'}),
            'formula_Level_4': forms.Select(attrs={'class': 'form-select'}),
        }        

class WorkstreamAssetHierarchyForm(forms.ModelForm):
    class Meta:
        model = Workstream
        fields = ('formula_Level_1', 'formula_Level_2', 'formula_Level_3', 'formula_Level_4', 'functions', 'SavingType', )
        
class InitiativeForm2(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    problem_statement = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    overallstatuscommentary = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    
    class Meta:
        model = Initiative

        fields = ['initiative_name', 'description', 'problem_statement', 'overallstatuscommentary', 
                'Workstream', 'initiativesponsor', 'workstreamsponsor', 'workstreamlead', 'financesponsor', 
                'Yearly_Planned_Value', 'Yearly_Forecast_Value', 'Yearly_Actual_value', 'Planned_Date', 
                'Plan_Relevance', 'L0_Completion_Date_Planned', 'L1_Completion_Date_Planned', 'L2_Completion_Date_Planned', 
                'L3_Completion_Date_Planned', 'L4_Completion_Date_Planned', 'L5_Completion_Date_Planned', 
                'actual_Lgate', 'Approval_Status', 'HashTag', 'overall_status', 'mark_as_confidential', 
                'activate_initiative_approvers', 'discipline', 'enabledby', 'currency', 'YYear', 'note', ]
        widgets = {
            'initiative_name': forms.TextInput(attrs={'placeholder': 'Initiative Name'}),
            'L0_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerLO_Plan'}), 
            'L1_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL1_Plan'}), 
            'L2_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL2_Plan'}), 
            'L3_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL3_Plan'}), 
            'L4_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL4_Plan'}), 
            'L5_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL5_Plan'}),
            
            # 'description': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
            # 'problem_statement': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
            # 'overallstatuscommentary': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
        }
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['Plan_Relevance'].widget.attrs.update({'id': 'id_plan_relevance'})
    #     # labels = {
    #     #     'description': 'description',
    #     #     'problem_statement':'problem_statement',
    #     #     'overallstatuscommentary':'overallstatuscommentary',
    #     # }

class InitiativeForm2Users(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    problem_statement = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    overallstatuscommentary = forms.CharField(widget=CKEditorUploadingWidget(), required=False)
    
    class Meta:
        model = Initiative

        fields = ('initiative_name', 'description', 'problem_statement', 'overallstatuscommentary', 
                'Workstream', 'initiativesponsor', 'workstreamsponsor', 'workstreamlead', 'financesponsor', 
                'Yearly_Planned_Value', 'Yearly_Forecast_Value', 'Yearly_Actual_value', 'Planned_Date', 
                'Plan_Relevance', 'L0_Completion_Date_Planned', 'L1_Completion_Date_Planned', 'L2_Completion_Date_Planned', 
                'L3_Completion_Date_Planned', 'L4_Completion_Date_Planned', 'L5_Completion_Date_Planned', 
                'Approval_Status', 'HashTag', 'overall_status', 'mark_as_confidential', 
                'activate_initiative_approvers', 'discipline', 'enabledby', 'currency', 'YYear', 'note', )
        widgets = {
            'initiative_name': forms.TextInput(attrs={'placeholder': 'Initiative Name'}),
            'L0_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerLO_Plan'}), 
            'L1_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL1_Plan'}), 
            'L2_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL2_Plan'}), 
            'L3_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL3_Plan'}), 
            'L4_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL4_Plan'}), 
            'L5_Completion_Date_Planned': DatePickerInput(options={"format": "DD/MM/YYYY"}, attrs={'id': 'dtPickerL5_Plan'}),
            
            # 'description': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
            # 'problem_statement': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
            # 'overallstatuscommentary': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
        }
      
class InitiativeForm3(forms.ModelForm):
    class Meta:
        model = Initiative

        fields = ('DocumentLink', 'SharepointUrl',)
        widgets = {
            'DocumentLink': forms.TextInput(attrs={'placeholder': 'Document Link'}),
            'SharepointUrl': forms.TextInput(attrs={'placeholder': 'Sharepoint Url'}),
        }
        
class InitiativeApprovalsForm(forms.ModelForm):
    class Meta:
        model = InitiativeApprovals
        fields = ()

class InitiativeApprovalsForm2(forms.ModelForm):
    class Meta:
        model = InitiativeApprovals
        fields = ('comments', )
        
class InitiativeNextLGateForm(forms.ModelForm):
    class Meta:
        model = Initiative
        fields = ('next_Lgate_Comment',)
        
class InitiativeImpactForm(forms.ModelForm):
    class Meta:
        model = InitiativeImpact

        fields = ('frequency', 'benefittype',
                'Jan_Plan', 'Feb_Plan', 'Mar_Plan', 'Apr_Plan', 'May_Plan', 'Jun_Plan',
                'Jul_Plan', 'Aug_Plan', 'Sep_Plan', 'Oct_Plan', 'Nov_Plan', 'Dec_Plan',
                
                'Jan_Forecast', 'Feb_Forecast', 'Mar_Forecast', 'Apr_Forecast', 'May_Forecast', 'Jun_Forecast', 
                'Jul_Forecast', 'Aug_Forecast', 'Sep_Forecast', 'Oct_Forecast', 'Nov_Forecast', 'Dec_Forecast',
                
                'Jan_Actual', 'Feb_Actual', 'Mar_Actual', 'Apr_Actual', 'May_Actual', 'Jun_Actual', 
                'Jul_Actual', 'Aug_Actual', 'Sep_Actual', 'Oct_Actual', 'Nov_Actual', 'Dec_Actual', 
                'YYear')
        
        widgets = {
            'frequency': forms.Select(attrs={'class':'form-select'}), 
            'benefittype': forms.Select(attrs={'class':'form-select'}),
            'YYear': forms.Select(attrs={'class':'form-select'}),

            'Jan_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Jan_Plan'}),
            'Feb_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Feb_Plan'}),
            'Mar_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Mar_Plan'}),
            'Apr_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Apr_Plan'}),
            'May_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'May_Plan'}),
            'Jun_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Jun_Plan'}),
            'Jul_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Jul_Plan'}),
            'Aug_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Aug_Plan'}),
            'Sep_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Sep_Plan'}),
            'Oct_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Oct_Plan'}),
            'Nov_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Nov_Plan'}),
            'Dec_Plan': forms.TextInput(attrs={'class':'form-control', 'id':'Dec_Plan'}),

            'Jan_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Jan_Forecast'}),
            'Feb_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Feb_Forecast'}),
            'Mar_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Mar_Forecast'}),
            'Apr_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Apr_Forecast'}),
            'May_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'May_Forecast'}),
            'Jun_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Jun_Forecast'}),
            'Jul_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Jul_Forecast'}),
            'Aug_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Aug_Forecast'}),
            'Sep_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Sep_Forecast'}),
            'Oct_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Oct_Forecast'}),
            'Nov_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Nov_Forecast'}),
            'Dec_Forecast': forms.TextInput(attrs={'class':'form-control', 'id':'Dec_Forecast'}),

            'Jan_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Jan_Actual'}),
            'Feb_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Feb_Actual'}),
            'Mar_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Mar_Actual'}),
            'Apr_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Apr_Actual'}),
            'May_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'May_Actual'}),
            'Jun_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Jun_Actual'}),
            'Jul_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Jul_Actual'}),
            'Aug_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Aug_Actual'}),
            'Sep_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Sep_Actual'}),
            'Oct_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Oct_Actual'}),
            'Nov_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Nov_Actual'}),
            'Dec_Actual': forms.TextInput(attrs={'class':'form-control', 'id':'Dec_Actual'}),
        }

        


        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance and self.instance.Jan_Plan:
                self.fields['Jan_Plan'].initial = "{:,.2f}".format(self.instance.Jan_Plan)

            if self.instance and self.instance.Feb_Plan:
                self.fields['Feb_Plan'].initial = "{:,.2f}".format(self.instance.Feb_Plan)

            if self.instance and self.instance.Mar_Plan:
                self.fields['Mar_Plan'].initial = "{:,.2f}".format(self.instance.Mar_Plan)

            if self.instance and self.instance.Apr_Plan:
                self.fields['Apr_Plan'].initial = "{:,.2f}".format(self.instance.Apr_Plan)

            if self.instance and self.instance.May_Plan:
                self.fields['May_Plan'].initial = "{:,.2f}".format(self.instance.May_Plan)

            if self.instance and self.instance.Jun_Plan:
                self.fields['Jun_Plan'].initial = "{:,.2f}".format(self.instance.Jun_Plan)

            if self.instance and self.instance.Jul_Plan:
                self.fields['Jul_Plan'].initial = "{:,.2f}".format(self.instance.Jul_Plan)

            if self.instance and self.instance.Aug_Plan:
                self.fields['Aug_Plan'].initial = "{:,.2f}".format(self.instance.Aug_Plan)

            if self.instance and self.instance.Sep_Plan:
                self.fields['Sep_Plan'].initial = "{:,.2f}".format(self.instance.Sep_Plan)

            if self.instance and self.instance.Oct_Plan:
                self.fields['Oct_Plan'].initial = "{:,.2f}".format(self.instance.Oct_Plan)

            if self.instance and self.instance.Nov_Plan:
                self.fields['Nov_Plan'].initial = "{:,.2f}".format(self.instance.Nov_Plan)

            if self.instance and self.instance.Dec_Plan:
                self.fields['Dec_Plan'].initial = "{:,.2f}".format(self.instance.Dec_Plan)

            # Forecast
            if self.instance and self.instance.Jan_Forecast:
                self.fields['Jan_Forecast'].initial = "{:,.2f}".format(self.instance.Jan_Forecast)

            if self.instance and self.instance.Feb_Forecast:
                self.fields['Feb_Forecast'].initial = "{:,.2f}".format(self.instance.Feb_Forecast)

            if self.instance and self.instance.Mar_Forecast:
                self.fields['Mar_Forecast'].initial = "{:,.2f}".format(self.instance.Mar_Forecast)

            if self.instance and self.instance.Apr_Forecast:
                self.fields['Apr_Forecast'].initial = "{:,.2f}".format(self.instance.Apr_Forecast)

            if self.instance and self.instance.May_Forecast:
                self.fields['May_Forecast'].initial = "{:,.2f}".format(self.instance.May_Forecast)

            if self.instance and self.instance.Jun_Forecast:
                self.fields['Jun_Forecast'].initial = "{:,.2f}".format(self.instance.Jun_Forecast)

            if self.instance and self.instance.Jul_Forecast:
                self.fields['Jul_Forecast'].initial = "{:,.2f}".format(self.instance.Jul_Forecast)

            if self.instance and self.instance.Aug_Forecast:
                self.fields['Aug_Forecast'].initial = "{:,.2f}".format(self.instance.Aug_Forecast)

            if self.instance and self.instance.Sep_Forecast:
                self.fields['Sep_Forecast'].initial = "{:,.2f}".format(self.instance.Sep_Forecast)

            if self.instance and self.instance.Oct_Forecast:
                self.fields['Oct_Forecast'].initial = "{:,.2f}".format(self.instance.Oct_Forecast)

            if self.instance and self.instance.Nov_Forecast:
                self.fields['Nov_Forecast'].initial = "{:,.2f}".format(self.instance.Nov_Forecast)

            if self.instance and self.instance.Dec_Forecast:
                self.fields['Dec_Forecast'].initial = "{:,.2f}".format(self.instance.Dec_Forecast)

            # Actual
            if self.instance and self.instance.Jan_Actual:
                self.fields['Jan_Actual'].initial = "{:,.2f}".format(self.instance.Jan_Actual)

            if self.instance and self.instance.Feb_Actual:
                self.fields['Feb_Actual'].initial = "{:,.2f}".format(self.instance.Feb_Actual)

            if self.instance and self.instance.Mar_Actual:
                self.fields['Mar_Actual'].initial = "{:,.2f}".format(self.instance.Mar_Actual)

            if self.instance and self.instance.Apr_Actual:
                self.fields['Apr_Actual'].initial = "{:,.2f}".format(self.instance.Apr_Actual)

            if self.instance and self.instance.May_Actual:
                self.fields['May_Actual'].initial = "{:,.2f}".format(self.instance.May_Actual)

            if self.instance and self.instance.Jun_Actual:
                self.fields['Jun_Actual'].initial = "{:,.2f}".format(self.instance.Jun_Actual)

            if self.instance and self.instance.Jul_Actual:
                self.fields['Jul_Actual'].initial = "{:,.2f}".format(self.instance.Jul_Actual)

            if self.instance and self.instance.Aug_Actual:
                self.fields['Aug_Actual'].initial = "{:,.2f}".format(self.instance.Aug_Actual)

            if self.instance and self.instance.Sep_Actual:
                self.fields['Sep_Actual'].initial = "{:,.2f}".format(self.instance.Sep_Actual)

            if self.instance and self.instance.Oct_Actual:
                self.fields['Oct_Actual'].initial = "{:,.2f}".format(self.instance.Oct_Actual)

            if self.instance and self.instance.Nov_Actual:
                self.fields['Nov_Actual'].initial = "{:,.2f}".format(self.instance.Nov_Actual)

            if self.instance and self.instance.Dec_Actual:
                self.fields['Dec_Actual'].initial = "{:,.2f}".format(self.instance.Dec_Actual)
    

    def __init__(self, *args, current_year=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate choices dynamically, if needed
        year_range = get_years() #range(2000, 2031)
        self.fields['YYear'].choices = [(y, y) for y in year_range]

        # Set initial value
        if current_year:
            self.initial['YYear'] = current_year

    def get_years():
        date_range = 7 
        this_year = datetime.now().year
        return {range(this_year - date_range, this_year + date_range)}



class FileForm(forms.ModelForm):
    class Meta:
        model = InitiativeFiles
        fields = ['initiativeFiles',]
        # widgets = {
        #     'initiativeFiles': ClearableFileInput(attrs={'multiple': True}),
        # }


class NoteForm(forms.ModelForm):
    Notes = forms.CharField(widget=CKEditorUploadingWidget())
    
    class Meta:
        model = InitiativeNotes
        fields = ['title', 'Notes',]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Note Title'}),
            #'Notes': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
        }
        # labels = {
        #     'Notes': 'Notes',
        # }

class ActualLgateForm(forms.ModelForm):
    class Meta:
        model = Actual_L_Gate
        fields = ['LGate', 'GateIndex']

class PredefinedApproversForm(forms.ModelForm):
    class Meta:
        model = PredefinedApprovers
        fields = ['Workstream', 
                  'workstreamsponsor', 'workstreamlead', 'financesponsor', 
                  'workstreamsponsor2', 'workstreamlead2', 'financesponsor2', 
                  'workstreamsponsor3', 'workstreamlead3', 'financesponsor3']#'actual_Lgate', 


class MTOScoringForm(forms.ModelForm):
    class Meta:
        model = MTOScoring
        fields = ['initiative', 'A0', 'B0', 'C0', 'D0', 'E0', 
                  'A1', 'B1', 'C1', 'D1', 'E1',
                  'A2', 'B2', 'C2', 'D2', 'E2',
                  'A3', 'B3', 'C3', 'D3', 'E3',
                  'A4', 'B4', 'C4', 'D4', 'E4',
                  'A5', 'B5', 'C5', 'D5', 'E5',]  
                 
                  
class MTOScoringInfoForm(forms.ModelForm):
    class Meta:
        model = MTOScoringInfo
        fields = ['initiative', 'proactive', 'proactiveType', 'likelyhoodAssetConsequence', 'severityJustification', 'likehoodJustification', 'mtoScore', ]

class MTORiskAssessmentForm(forms.ModelForm):
    likelihood_justification = forms.CharField(widget=CKEditorUploadingWidget())
    impact_justification = forms.CharField(widget=CKEditorUploadingWidget())
    
    class Meta:
        model = Initiative
        fields = [
            'asset_consequences',
            'asset_consequence', 
            'likelihood_asset_consequence',
            
            'people_consequence',
            'likelihood_people_consequence', 
            
            'community_consequence', 
            'likelihood_community_consequence',
             
            'environmental_consequence', 
            'likelihood_environment_consequence', 
            
            'primary_ram_box', 
            'primary_ram_color', 
            'second_ram_box', 
            'second_ram_color', 
            'highest_impact_category', 
            'second_highest_impact_category',
            
            'likelihood_justification',
            'impact_justification',
            
            'proactive_type',
        ]
        # widgets = {
        #     'likelihood_justification': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
        #     'impact_justification': CKEditor5Widget(attrs={"class": "django_ckeditor_5"}, config_name="default"),
        # }
        # labels = {
        #     'likelihood_justification': 'likelihood_justification',
        #     'impact_justification':'impact_justification',
        # }
        
class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'UOM', 'rated_capacity', 'margin', 'active',]

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title', 'image', 'is_active', 'url',]