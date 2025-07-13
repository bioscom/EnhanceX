from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.db.models import Q, F, Prefetch
from django.db import connection
from simple_salesforce import Salesforce
from django.db import models
from .utils import fetch_salesforce_report
from reports.forms import *
import traceback
import logging
from django.contrib import messages
from django.utils.crypto import get_random_string
from Fit4.models import *
from dashboard.models import *
#import pandas as pd 
from django.http import HttpResponse
from openpyxl import Workbook
from Fit4.forms import *

from django.contrib.auth.decorators import login_required

from django_filters import rest_framework as filters
from rest_framework import generics
from reports.filters import *

import json
from django.core.serializers.json import DjangoJSONEncoder

from urllib.parse import urlparse
from urllib.parse import parse_qs

from django.db.models.functions import Substr
import pandas as pd
from django.core.mail import mail_admins

# Report Landing Home Page
@login_required(login_url='account:login_page')
def home_report(request):
    oReports = SavedFilter.objects.all()
    #form = ReportForm2(request.POST)
    
    formPlanRelevance = PlanRelevance.objects.all() 
    formDiscipline = Discipline.objects.filter()
    formCategory = report_category.objects.filter()
    formSavingType = SavingsType.objects.filter()
    formFunction = Functions.objects.filter()
    #formReportFilter = Report_Filter_parameters.objects.filter().order_by('filter_name')
    formYear = Initiative.objects.order_by('YYear').values_list('YYear', flat=True).distinct()
    
    #header = [field.name for field in Initiative._meta.fields if field.name != 'id']
    rows = Initiative.objects.all() 
    #return render(request, 'report.html', {'headers': header, 'rows':rows})
    
    return render(request, 'Home.html', {'oReports': oReports, 'formCategory':formCategory,'formPlanRelevance':formPlanRelevance, 
                                        'formDiscipline':formDiscipline, 'formSavingType':formSavingType, 
                                        'formFunction':formFunction, 'formYear':formYear}) #, 'reportForm': form, 'formReportFilter':formReportFilter

def created_by_me_report(request):
    oReports = SavedFilter.objects.filter(created_by=request.user)
    #form = ReportForm2(request.POST)
    
    formPlanRelevance = PlanRelevance.objects.all() 
    formDiscipline = Discipline.objects.filter()
    formCategory = report_category.objects.filter()
    formSavingType = SavingsType.objects.filter()
    formFunction = Functions.objects.filter()
    #formReportFilter = Report_Filter_parameters.objects.filter().order_by('filter_name')
    formYear = Initiative.objects.order_by('YYear').values_list('YYear', flat=True).distinct()
    
    #header = [field.name for field in Initiative._meta.fields if field.name != 'id']
    rows = Initiative.objects.all() 
    #return render(request, 'report.html', {'headers': header, 'rows':rows})
    
    return render(request, 'Home.html', {'oReports': oReports, 'formCategory':formCategory,'formPlanRelevance':formPlanRelevance, 
                                        'formDiscipline':formDiscipline, 'formSavingType':formSavingType, 
                                        'formFunction':formFunction, 'formYear':formYear}) #, 'reportForm': form, 'formReportFilter':formReportFilter
    
def created_by_others(request):
    oReports = SavedFilter.objects.exclude(created_by=request.user)
    #form = ReportForm2(request.POST)
    
    formPlanRelevance = PlanRelevance.objects.all() 
    formDiscipline = Discipline.objects.filter()
    formCategory = report_category.objects.filter()
    formSavingType = SavingsType.objects.filter()
    formFunction = Functions.objects.filter()
    #formReportFilter = Report_Filter_parameters.objects.filter().order_by('filter_name')
    formYear = Initiative.objects.order_by('YYear').values_list('YYear', flat=True).distinct()
    
    #header = [field.name for field in Initiative._meta.fields if field.name != 'id']
    rows = Initiative.objects.all() 
    #return render(request, 'report.html', {'headers': header, 'rows':rows})
    
    return render(request, 'Home.html', {'oReports': oReports, 'formCategory':formCategory,'formPlanRelevance':formPlanRelevance, 
                                        'formDiscipline':formDiscipline, 'formSavingType':formSavingType, 
                                        'formFunction':formFunction, 'formYear':formYear}) #, 'reportForm': form, 'formReportFilter':formReportFilter

# This is where a report is created
def report_filter(request, category_id):
    #where category_id is the category id of the report category
    form = SavedFilterForm(request.POST)
    cat = report_category.objects.get(id=category_id)
    initfilter = InitiativeFilter(request.GET, queryset=Initiative.objects.select_related('unit', 'author').order_by('-Created_Date'))
    impactfilter = InitiativeImpactFilter(request.GET, queryset=InitiativeImpact.objects.select_related('initiative', 'benefittype'))
    return render(request, 'report_filter.html', {'filter': initfilter, 'impactfilter':impactfilter, 'cat':cat, 'form':form})


#@login_required(login_url='account:login')
def edit_filter(request, filter_id):
    #saved_report = get_object_or_404(SavedFilter, unique_name=filter_id)
    oReport = SavedFilter.objects.get(unique_name=filter_id) # Get the report to be updated
    print(oReport.filter_params2)
    filterset = InitiativeFilter(oReport.filter_params2, queryset=Initiative.objects.all())
    impactfilter = InitiativeImpactFilter(oReport.filter_params2, queryset=InitiativeImpact.objects.all())
    #oReport = SavedFilter.objects.get(unique_name=filter_id) # Get the report to be updated

    try:
        if request.method == "POST":
            reportForm = SavedFilterForm(data=request.POST, instance=oReport)
            oReport.filter_params=request.META['HTTP_REFERER'] #filter_data.qs
            all_selected={key:request.GET.getlist(key) for key in request.GET.keys()}
            oReport.filter_params2=all_selected #request.GET.getlist("Workstream")
            oReport.name = request.POST.get('name')
            oReport.save()
            #return redirect('/en/reports/home')
            return redirect('/en/reports/'+ filter_id +'/view')
        else:
            reportForm = SavedFilterForm(instance=oReport)
    except Exception as e:
        print(traceback.format_exc()) 
    return render(request, 'report_filter_edit.html', {'filter':filterset, 'impactfilter':impactfilter, 'oReports':oReport, 'reportForm':reportForm})

def fetch_metadata(request):
    filter_val = request.GET.get('filter')
    # Example: get the latest initiative for the given filter
    o = SavedFilter.objects.filter(filter_params2=filter_val).first()

    if o:
        metadata = o.filter_params2  # Assume this is a model field
    else:
        metadata = "No data found"
    return JsonResponse({'metadata': metadata})

#@login_required(login_url='account:login_page')
def save_filter(request, category_id):
    cat = report_category.objects.get(id=category_id)
    queryset = SavedFilter.objects.all()

    if request.method == "POST":
        report_name = request.POST.get("name")
        if report_name:
           o = SavedFilter.objects.create(
                created_by=request.user,
                name=report_name,
                filter_params=request.META['HTTP_REFERER'], #filter_data.qs
                filter_params2={key:request.GET.getlist(key) for key in request.GET.keys()}, #request.GET.dict(),
                unique_name=get_random_string(length=32), 
                category=cat
            )
        return redirect('/en/reports/' + o.unique_name + '/view') # Redirect to report created list
    return render(request, "Home.html")
    #return render(request, "Home.html", { "filterset": filterset, "saved_reports": SavedFilter.objects.filter(created_by = request.user), })

@login_required(login_url='account:login_page')
def save_as(request, filter_id):
    oFilter = SavedFilter.objects.get(unique_name=filter_id)
    if request.method == "POST":
        report_name = request.POST.get("name")
        description = request.POST.get("description")

        saved_filter = SavedFilter.objects.create(
            created_by=request.user, 
            name=report_name, 
            filter_params=oFilter.filter_params, 
            filter_params2=oFilter.filter_params2, 
            unique_name=get_random_string(length=32),
            category=oFilter.category,
            description=description)

        return redirect('/en/reports/'+ saved_filter.unique_name +'/view') # Redirect to saved reports list
    return render(request, 'report_view.html')


#@login_required(login_url='account:login')
def add_savedfilter_todashboard(request, filter_id):
    oFilter = SavedFilter.objects.get(unique_name=filter_id)
    try:
        if request.method == "POST":
            dashboard_name = request.POST.get("name")
            description = request.POST.get("description")

            if oFilter.filter_params2 != None:
                odashboard = dashboards.objects.create(
                    created_by=request.user, 
                    last_modified_by = request.user,
                    filter = oFilter,
                    name=dashboard_name, 
                    unique_name=get_random_string(length=32),
                    description=description)
                return redirect('/en/dashboard/'+ odashboard.unique_name +'/view') # Redirect to saved reports list
            else:
                 messages.warning(request, 'Ensure you set report filters on the report before adding it to the Dashboard. <b>'+ oFilter.name + '</b> has no report filter.')
                 return redirect('/en/reports/'+ filter_id +'/view')

    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'report_view.html')

#@login_required(login_url='account:login')
def save_filter2(request, id):
    #where id id the category id of the report category
    cat = report_category.objects.get(id=id)
    if request.method == 'POST':
        filter_data = InitiativeFilter(request.GET, queryset=Initiative.objects.all())
        filter_name = request.POST.get('name')
        #filter_params = request.POST.get('filter_params')
        filter_params = request.META['HTTP_REFERER'] #filter_data.qs
        #filter_params = serialize_filter_data(filter_data.qs)
        
        # Save the filter
        saved_filter = SavedFilter.objects.create(
            created_by=request.user, 
            name=filter_name, 
            unique_name=get_random_string(length=32), 
            filter_params=filter_params, category=cat)
        return redirect('/en/reports/home')
    return render(request, 'Home.html')


@login_required(login_url='account:login_page')
def delete_filter(request, id):
    queryset = SavedFilter.objects.get(id=id)
    queryset.delete()
    return redirect('/en/reports/rhome')


# Individual Report View Page
#@login_required(login_url='account:login')
def report_view(request, report_id):
    oFilter = SavedFilter.objects.get(unique_name=report_id)
    reportForm = SavedFilterForm(instance=oFilter)
    RecordCount=0
    duped=[]
    
    try:
        #queryset=Initiative.objects.select_related().filter(**filter_params)
        if oFilter.filter_params2 != None:
            multi_valued_keys = ['Plan_Relevance', 'Workstream', 'overall_status', 'YYear', 'benefittype', 'enabledby', 'functions']
            for key in multi_valued_keys:
                if key in oFilter.filter_params2 and isinstance(oFilter.filter_params2[key], list):
                    oFilter.filter_params2[f"{key}__in"] = oFilter.filter_params2.pop(key)
                    
            queryset = InitiativeImpact.objects.select_related('initiative').annotate(
                Workstream=F('initiative__Workstream'),
                #HashTag=F('initiative__HashTag'),
                overall_status=F('initiative__overall_status'),
                Plan_Relevance=F('initiative__Plan_Relevance'),
                enabledby=F('initiative__enabledby'),
                functions=F('initiative__functions')).prefetch_related( 'initiative__Plan_Relevance', 'initiative__enabledby').filter(**oFilter.filter_params2)
            # Code below is used to select unique rows from the queryset. The queryset brings many rows based on the ManyToMany relationships in the model
            # If the database used was postgreSql, you could have used .distinct('field'). But MSSQL used here does not support .distinct('field').
            # So there needs to be a work around
            seen = set()
            deduped_initiatives = []
            for obj in queryset:
                key = (obj.initiative.initiative_id)
                if key not in seen:
                    seen.add(key)
                    deduped_initiatives.append(obj)

            duped = list(deduped_initiatives)

            RecordCount=len(duped)
        else:
            duped=[]
            RecordCount=0
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'report_view.html', {'oReport':oFilter, 'reportForm':reportForm, 'RecordCount':RecordCount, 'duped':duped})#, 'form':initiativeForm

#@login_required(login_url='account:login')
def category_list(request):
    catList = report_category.objects.all()
    try:
        if request.method == "POST":
            form = CategoryForm(request.POST)
            if form.is_valid():
                oCat = form.save(commit=False)
                oCat.created_by = request.user
                oCat.last_modified_by = request.user
                oCat.save()
                return redirect('/en/reports/report/cat')
        else:
            form = CategoryForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'report_category.html', {'form': form, 'catList': catList})

#region #@login_required(login_url='account:login')
# def add_report(request):
#     if request.method == "POST":
#         # form = ReportForm(request.POST)
#         data = request.POST
        
#         cat_id = data.get('category')

#         category = report_category.objects.get(id=cat_id)
#         name = data.get('name')
#         description = data.get('description', '')
        
#         WorkStream = data.get('Workstream')
#         wsFilters = data.get('wsFilter')
        
#         OverallStatus = data.getlist('OverallStatus') # os - overall status (Options)
#         osFilters = data.get('osFilter') # osFilter (Options)
        
#         discipline = data.getlist('discipline') # discipline (Options)
#         discFilter = data.get('discFilter') # discFilter
#         func = data.getlist('func') # func (Options)
#         funcFilter = data.get('funcFilter') # funcFilter
#         st = data.get('st') # st (Options)
#         stFilter = data.get('stFilter') # stFilter
        
#         pr = data.getlist('pr') # pr plan relevance
#         prFilter = data.get('prFilter') # prFilter
#         HashTag = data.get('HashTag') # HashTag
#         htFilter = data.get('htFilter') # htFilter
        
#         year = data.get('year') # year
        
#         report.objects.create(name=name, category=category, description=description, unique_name=get_random_string(length=32), 
#                             WorkStream=WorkStream, wsFilters=wsFilters, overall_status=OverallStatus, osFilters=osFilters, 
#                             discipline=discipline, discFilters=discFilter, Function=func, funcFilters=funcFilter, SavingType=st, 
#                             stFilters=stFilter, Plan_Relevance=pr, psFilters=prFilter, HashTag=HashTag, 
#                             htFilters=htFilter, created_by=request.user, last_modified_by=request.user, YYear=year)
#         return redirect('/en/reports/report/home')
#     #     else:
#     #         form = ReportForm()
#     # except Exception as e:
#     #     print(traceback.format_exc())
#endregion     # return render(request, 'partial_add_report.html', {'form': form})

#@login_required(login_url='account:login')
def edit_category(request, id):
    catList = report_category.objects.all()
    try:
        oCat = report_category.objects.get(id=id)
        if request.method == "POST":
            form = CategoryForm(data=request.POST, instance=oCat)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()
                return redirect('/en/reports/report/cat')
        else:
            form = CategoryForm(instance=oCat)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'report_edit_category.html', {'form': form, 'catList': catList})

def is_valid_queryParam(param):
    return param != '' and param is not None