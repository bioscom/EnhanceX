import django_filters
from django_filters import rest_framework as filters, CharFilter, NumberFilter
from Fit4.models import * 
from django import forms

from django.db.models import Q
from django.db.models import Value as V
from django.db.models.functions import Concat
from django_filters.views import FilterView

class InitiativeFilter(filters.FilterSet):
    Workstream=django_filters.ModelMultipleChoiceFilter(queryset=Workstream.objects.all(), widget=forms.CheckboxSelectMultiple)
    overall_status=django_filters.ModelMultipleChoiceFilter(queryset=overall_status.objects.all(), widget=forms.CheckboxSelectMultiple)
    enabledby=django_filters.ModelMultipleChoiceFilter(queryset=EnabledBy.objects.all(), widget=forms.CheckboxSelectMultiple)
    Plan_Relevance=django_filters.ModelMultipleChoiceFilter(queryset=PlanRelevance.objects.all(), widget=forms.CheckboxSelectMultiple)
    functions=django_filters.ModelMultipleChoiceFilter(queryset=Functions.objects.all(), widget=forms.CheckboxSelectMultiple)
    # YYear=django_filters.ModelMultipleChoiceFilter(queryset=Initiative.objects.values_list('YYear', flat=True).order_by().distinct(), widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = Initiative
        fields = [
            'Workstream',
            #'Workstream__workstreamname',
            'initiative_name',
            'initiative_id',
            'author', 
            'initiativesponsor', 
            'workstreamsponsor', 
            'workstreamlead', 
            'financesponsor', 
            'Planned_Date',  
            'Plan_Relevance', 
            'actual_Lgate', 
            'Approval_Status',  
            #'HashTag', 
            'overall_status', 
            'enabledby', 
            'YYear', 
            'L0_Completion_Date_Planned', 
            'L1_Completion_Date_Planned', 
            'L2_Completion_Date_Planned', 
            'L3_Completion_Date_Planned',
            'L4_Completion_Date_Planned', 
            'L5_Completion_Date_Planned', 
            'SavingType', 
            'functions', 
            'discipline', 
            'formula_Level_1', 
            'formula_Level_2', 
            'formula_Level_3', 
            'formula_Level_4', 
            'unit',
            'Created_Date',
        ]
        
        filter_overrides = {
            models.CharField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
            models.IntegerField: {
                'filter_class': filters.NumberFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
            models.BooleanField: {
                'filter_class': filters.BooleanFilter,
                'extra': lambda f: {
                    'widget': forms.CheckboxInput,
                },
            },
        }
    
    def filter_by_workstream(self, queryset, name, value):
        return queryset.filter(Q(initiativeId__Workstream__icontains=value))
        
        # @property
        # def qs(self):
        #     parent = super().qs
        #     author = getattr(self.request, 'user', None)

        #     return parent.filter(is_published=True) \
        #         | parent.filter(author=author)

class InitiativeImpactFilter(filters.FilterSet):
    benefittype=django_filters.ModelMultipleChoiceFilter(queryset=BenefitType.objects.all(), widget=forms.CheckboxSelectMultiple)
    YYear=django_filters.ModelMultipleChoiceFilter(queryset=InitiativeImpact.objects.values_list('YYear', flat=True).order_by('-YYear').distinct(), widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = InitiativeImpact
        fields = [
            'benefittype', 'YYear', 
            ]
        filter_overrides = {
            models.CharField: {
                'filter_class': filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
            models.IntegerField: {
                'filter_class': filters.NumberFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
            models.BooleanField: {
                'filter_class': filters.BooleanFilter,
                'extra': lambda f: {
                    'widget': forms.CheckboxInput,
                },
            },
        }