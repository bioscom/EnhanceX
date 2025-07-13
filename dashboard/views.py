from .models import *
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.db import models
from django.db.models import Q, F, Prefetch
from dashboard.forms import *
import traceback
from django.utils.crypto import get_random_string
from Fit4.models import *
from reports.models import *
import pandas as pd
from django.shortcuts import render

from datetime import datetime, timedelta, date

from django.contrib import messages

from .views_mto_dashboard import *
from .views_dashboard_plotly_graphs import *

from .view_delivery_report import *
from .view_opex_report import *

from django.db.models.functions import TruncMonth
from collections import defaultdict
import calendar
import hashlib

def get_color_from_label(label):
    # Generate a color hex from a hash of the label
    hex_color = hashlib.md5(label.encode()).hexdigest()[:6]
    return f'#{hex_color}'

# Report Landing Home Page
def home_dashboard(request):
    oDashboard = dashboards.objects.all()
    dashboardForm = DashboardForm(request.POST)
    recordCount = oDashboard.count()
    # workstream = Workstream.objects.all()
    # allUsers = User.objects.all()
    # functions = Functions.objects.all()
    # savingsType = SavingsType.objects.all()
    # recordType = record_type.objects.all()

    # level1 = Formula_Level_1.objects.all()
    # level2 = Formula_Level_2.objects.all()
    # level3 = Formula_Level_3.objects.all()
    # level4 = Formula_Level_4.objects.all()

    return render(request, 'index.html', {'form': dashboardForm, 'oDashboard': oDashboard, 'recordCount':recordCount })
    
    # return render(request, 'index.html', {'script': script, 'div': div, 'form': dashboardForm, 'oDashboard': oDashboard, 'recordCount':recordCount, 'allUsers':allUsers, 
    #                                       'workstream':workstream, 'functions':functions, 'savingsType':savingsType, 'recordType':recordType,
    #                                       'level1':level1, 'level2':level2, 'level3':level3, 'level4':level4, })

def add_dashboard(request):
    try:
        if request.method == "POST":
            form = DashboardForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.created_by = request.user
                o.last_modified_by = request.user
                o.unique_name = get_random_string(length=32)
                o.save()
                # Update Currency in Initiative
                return redirect('/en/dashboard')
        else:
            form = DashboardForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partial_add_dashboard.html", {'form': form})

def edit_dashboard(request, id):
    try:
        oDash = dashboards.objects.get(id=id)
        if request.method == "POST":
            form = DashboardForm(data=request.POST, instance=oDash)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()

                return redirect('/en/dashboard/'+ oDash.unique_name +'/view')
        else:
            form = DashboardForm(data=request.POST, instance=oDash)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partial_edit_dashboard.html", {'form': form})

def delete_dashboard(request, id):
    queryset = dashboards.objects.get(id=id)
    queryset.delete()
    return redirect('/en/dashboard')

# Find all "error" cells (e.g., NaN, negative numbers, wrong types)


# Individual Report View Page
def dashboard_view(request, dashboard_id):
    oDashboard = get_object_or_404(dashboards, unique_name=dashboard_id) #dashboards.objects.get(unique_name=dashboard_id)
    oDashboardForm = DashboardForm(instance=oDashboard)
    
    oFilter = get_object_or_404(SavedFilter, id=oDashboard.filter.id) #SavedFilter.objects.get(id=oDashboard.filter.id)
    if oFilter.filter_params2 != None:
        multi_valued_keys = ['Plan_Relevance', 'Workstream', 'overall_status', 'YYear', 'benefittype', 'enabledby']
        for key in multi_valued_keys:
            if key in oFilter.filter_params2 and isinstance(oFilter.filter_params2[key], list):
                oFilter.filter_params2[f"{key}__in"] = oFilter.filter_params2.pop(key)
                
    
        print(oFilter.filter_params2)
        queryset=InitiativeImpact.objects.select_related('initiative').annotate(
            Workstream=F('initiative__Workstream'),
            WorkstreamName=F('initiative__Workstream__workstreamname'),
            #HashTag=F('initiative__HashTag'),
            functions=F('initiative__functions__title'),
            Year=F('initiative__YYear'),
            overall_status=F('initiative__overall_status'),
            Plan_Relevance=F('initiative__Plan_Relevance'), 
            ActualLGate=F('initiative__actual_Lgate__LGate'),
            enabledby=F('initiative__enabledby')).prefetch_related('initiative__Plan_Relevance').filter(**oFilter.filter_params2).values()
        
        if queryset.exists():
            pd.set_option('display.max_columns', None)
            df=pd.DataFrame(list(queryset))
            df=df.drop(columns=['last_modified_date', 'Created_Date'])

            # df=df.drop(columns=['last_modified_date', 'Created_Date', 'Planned_Date',\
            #                     'L0_Completion_Date_Planned', 'L1_Completion_Date_Planned', 'L2_Completion_Date_Planned', 'L3_Completion_Date_Planned', 'L4_Completion_Date_Planned', 'L5_Completion_Date_Planned',\
            #                     'L0_Completion_Date_Actual', 'L1_Completion_Date_Actual', 'L2_Completion_Date_Actual', 'L3_Completion_Date_Actual', 'L4_Completion_Date_Actual', 'L5_Completion_Date_Actual'])
            df.replace(to_replace=[None], value=0, inplace=True)
            df.fillna(0, inplace=True)

            print(df)

            doughnutPlan = doughnutPlanChart(df)
            doughnutActual = doughnutActualChart(df)
            bar = VerticalBarChart(df)
            hBar = HorizontalBarChart(df)
            byFunctions=VerticalBarChartByFunctions(df)
            byLGate = VerticalBarChartByLGates(df)
            countByLGate = ChartCountByLGates(df)
            graph_json = VerticalBarChartByInLast7Days(request)
        else:
            doughnutPlan = []
            doughnutActual = []
            bar =[]
            hBar =[]
            byFunctions=[]
            byLGate = []
            countByLGate = []
    return render(request, 'dashboard_view.html', {'doughnut_chart': doughnutPlan, 'doughnut_chart2': doughnutActual, 'bar_chart':bar,'Lgate_chart':byLGate,
                                                   'hbar_chart':hBar, 'function_chart':byFunctions, 'LGate_Count':countByLGate, 
                                                  'oDashboard':oDashboard, 'oDashboardForm':oDashboardForm, 'graph_json': graph_json})#, 'table':table_html "graph_json": graph_json,

def dashboard_view2(request, dashboard_id):
    oDashboard = dashboards.objects.get(unique_name=dashboard_id)
    oDashboardForm = DashboardForm(instance=oDashboard)
    return render(request, "dashboard.html", {'oDashboard':oDashboard, 'oDashboardForm':oDashboardForm})


#region ================================ MTO Dashboard Reporting ==========================================================================

# # of MTO Actions Overdue with summary
# Open MTO Actions Due within 30 days
# Threats and Opportunities Due in 30 days

# Overdue Threats and Opportunities
# Top 20 Threats & Opportunities (L3 - L5)
# Threats & Opportunities at L0 to L2

# KPI1: New Threats & Opportunity
# KPI3: Resolved Threats & Opportunity
# KPI4: Overdue Threats & Opportunity
# MTO KPI5 - Total Threats/Opportunity Score

def dashboard_MTO(request):
    #yyear=int(request.POST.get('year_select') or datetime.now().year)
    yyear=request.POST.get('year_select')
    unit=request.POST.get('unit_select')
    recordType=request.POST.get('recordType_select')
    workstream=request.POST.get('workstream_select')
    
    workstreamName=unitName=recordTypeName=""
    workstreamName = (
        Workstream.objects.filter(id=workstream).values_list("workstreamname", flat=True).first()
        if workstream else None
    )
    
    unitName = (
        Unit.objects.filter(id=unit).values_list("name", flat=True).first()
        if unit else None
    )
        
    recordTypeName = (
        record_type.objects.filter(id=recordType).values_list("name", flat=True).first()
        if recordType else None
    )
        
    # if recordType:     
    #     recordTypeName = record_type.objects.get(id=recordType).name
    # else:
    #     recordTypeName
    
    initiatives = Initiative.objects.filter()

    oWorkstream=Workstream.objects.filter(workstreamname__icontains='MTO')
    rectType=record_type.objects.all()
    units=Unit.objects.filter(Q(active=True))
    selectedYears = get_years()
    
    # # Only one database query instead of four
    # statuses = action_status.objects.filter(name__in=["Completed", "On hold", "Defer", "Cancelled"])
    # status_map = {s.name: s for s in statuses}

    # ovrsC = status_map.get("Completed")
    # ovrsH = status_map.get("On hold")
    # ovrsD = status_map.get("Defer")
    # ovrsCa = status_map.get("Cancelled")
    try:
        ovrsC=action_status.objects.get(Q(name="Completed"))
        ovrsH=action_status.objects.get(Q(name="On hold"))
        ovrsCa=action_status.objects.get(Q(name="Cancelled"))
        
        initovrsC=overall_status.objects.get(Q(name="Completed"))
        initovrsH=overall_status.objects.get(Q(name="On hold"))
        initovrsD=overall_status.objects.get(Q(name="Defer"))
        initovrsCa=overall_status.objects.get(Q(name="Cancelled"))
    
        #1 of MTO Actions Overdue with summary
        overDueActions = actionsOverDue(yyear, unit, recordType, workstream, ovrsC, ovrsH, ovrsCa)
        
        #2 Open MTO Actions Due within 30 days                                                        
        actionsDueIn30Days = actionsOverDueIn30Days(yyear, unit, recordType, workstream, ovrsC, ovrsH, ovrsCa) 
                                                         
        #3 Threats and Opportunities Due in 30 days
        threatsIn30Days = threatsDueIn30Days(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)
        
        #4 Overdue Threats and Opportunities                     
        overDueThreatsOpportunity = OverDueThreatsOpportunity(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)
        
        #5 Top 20 Threats & Opportunities (L3 - L5)
        obj_top20Threats =top20ThreatsOpport(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)
        
        #6 Threats & Opportunities at L0 to L2                     
        threatOpportunityatL2=threatsOpportL2(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)                    
        
        #7 KPI1: New Threats & Opportunity
        newThreats=newThreatsOpportunity(initiatives, yyear, unit, recordType, workstream)
        labels_new_threats = newThreats['labels_new_threats']
        datasets_new_threats = newThreats['datasets_new_threats']
        
        #8 KPI3: Resolved Threats & Opportunity
        resolvedThreats=resolvedThreatsOpportunity(initiatives, yyear, unit, recordType, workstream)
        labels_resolved_threats = resolvedThreats['labels_resolved_threats']
        datasets_resolved_threats = resolvedThreats['datasets_resolved_threats']
        
        #9 KPI4: Overdue Threats & Opportunity
        overDueThreats=overDueThreatsOpportunities(initiatives, yyear, unit, recordType, workstream)
        labels_overDue_threats = overDueThreats['labels_overDue_threats']
        datasets_overDue_threats = overDueThreats['datasets_overDue_threats']
        
        #10 MTO KPI5 - Total Threats/Opportunity Score
        totalThreats=totalThreatsOpportunities(initiatives, yyear, unit, recordType, workstream)
        labels_total_threats=totalThreats['month_labels']
        active_data_total_threats=totalThreats['active_data']
        inactive_data_total_threats=totalThreats['inactive_data']
        sum_data_total_threats=totalThreats['sum_data']

        #11 All Active Threats and Opportunities
        page_obj = activeThreatsOpport(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)                           #11 All ACTIVE Threats and Opportunities Report 
    
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'mto_dashboard_view.html', {'page_obj':page_obj, 
                                                       'oWorkstream':oWorkstream, 
                                                       'rectType':rectType, 
                                                       'units':units, 
                                                       'selectedYears':selectedYears, 
                                                       'overDueActions':overDueActions,
                                                       'actionsDueIn30Days':actionsDueIn30Days,
                                                       'threatsIn30Days':threatsIn30Days,
                                                       'overDueThreatsOpportunity':overDueThreatsOpportunity,
                                                       'obj_top20Threats':obj_top20Threats,
                                                       'threatOpportunityatL2':threatOpportunityatL2, 
                                                       'yyear':yyear, 
                                                       'unit':unitName, 
                                                       'recordType':recordTypeName, 
                                                       'workstream':workstreamName, 
                                                       'labels_new_threats':labels_new_threats, 
                                                       'datasets_new_threats':datasets_new_threats,
                                                       'labels_overDue_threats':labels_overDue_threats,
                                                       'datasets_overDue_threats':datasets_overDue_threats,
                                                       'labels_resolved_threats':labels_resolved_threats,
                                                       'datasets_resolved_threats':datasets_resolved_threats,
                                                       
                                                       'labels_total_threats':labels_total_threats,
                                                       'active_data_total_threats':active_data_total_threats,
                                                       'inactive_data_total_threats':inactive_data_total_threats,
                                                       'sum_data_total_threats':sum_data_total_threats
                                                    })

#MTO


# def resolvedThreatsOpportunity():
#     pass

# def overdueThreatsOpportunity():
#     pass

def totalThreatsOpportunityScore():
    pass

#endregion =============================================================================================================================


#region ================================ Management Reporting ==========================================================================

def handle_weekly_report(request, model, show_current_func, show_last_func, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range):
    if model.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW).first():
        return show_current_func(request, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range)
    else:
        messages.warning(request, f"No record for the current week {oWeekTW}, click on sync this week data.")
        return show_last_func(request, oWeekLW, oYear, oWeeks, oFunction, year_range)
    
def opex_report(request, report_year=None, report_week=None):
    try:
        if request.method == "POST":
            selected_year = request.POST.get('selected_year')
            print(f"Selected via AJAX: {selected_year}")
        else:
            selected_year = datetime.now().year  # Default on GET
        
        today = datetime.now().today()
        oYear = today.year if not report_year or report_year == 'None' else report_year
        
        oWeekTW = today.isocalendar().week if not report_week or report_week == 'None' else report_week
        oWeekLW = oWeekTW - 1
        
        # First: your subset of report data
        report_subset = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW)

        # Then: filter Functions that are related to this subset
        oFunction = Functions.objects.filter(
            id__in=report_subset.values_list('functions', flat=True)
        ).distinct()
        
        #oFunction = Functions.objects.all() 
        
        return handle_weekly_report(request, opex_weekly_Initiative_Report, showOpexThisWeek, showOpexLastWeek, oWeekTW, oWeekLW, oYear, get_weeks_in_year(oYear), oFunction, list_years_from2018())
            
    except Exception as e:
        print(traceback.format_exc())   
    return redirect(reverse("Fit4:home"))

def delivery_report(request, report_year=None, report_week=None):
    try:
        if request.method == "POST":
            selected_year = request.POST.get('selected_year')
            print(f"Selected via AJAX: {selected_year}")
        else:
            selected_year = datetime.now().year  # Default on GET
        
        today = datetime.now().today()
        oYear = today.year if not report_year or report_year == 'None' else report_year
        #oFunction = Workstream.objects.all() # Function here is workstream. Different from opex module
        oWeekTW = today.isocalendar().week if not report_week or report_week == 'None' else report_week
        oWeekLW = oWeekTW - 1
        
        # First: your subset of report data
        report_subset = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW)

        # Then: filter Functions that are related to this subset
        oFunction = Workstream.objects.filter(
            id__in=report_subset.values_list('Workstream', flat=True)
        ).distinct()
        
        # Remove prefix from each title
        oFunction = [ws.workstreamname.replace("Renaissance Delivery - ", "") for ws in oFunction]
        
        
        return handle_weekly_report(request, delivery_weekly_Initiative_Report, showDeliveryThisWeek, showDeliveryLastWeek, oWeekTW, oWeekLW, oYear, get_weeks_in_year(oYear), oFunction, list_years_from2018())
    except Exception as e:
        print(traceback.format_exc())   
    return redirect(reverse("Fit4:home"))

#endregion =============================================================================================================================


# Use these lines to start any function in your application
# def module_name(request):
#     try:
#   
#    
#     except Exception as e:
#         print(traceback.format_exc())
#     return redirect(reverse("Fit4:home"))