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

# def get_weeks(year):
#     # First Monday of the year (or the first week starting on Monday)
#     d = datetime.date(year, 1, 1)
#     d += datetime.timedelta(days=(7 - d.weekday()) % 7)  # move to next Monday if not already Monday

#     weeks = []
#     try:
#         while d.year == year:
#             week_start = d
#             week_end = d + datetime.timedelta(days=6)
#             weeks.append((week_start, week_end))
#             d += datetime.timedelta(weeks=1)
#     except Exception as e:
#         print(traceback.format_exc())
#     return weeks

# def get_years():
#     date_range = 7 
#     current_year = datetime.now().year
#     return list(range(current_year - date_range, current_year + 1))

def get_weeks_in_year(year):
    # Find the first Monday of the ISO year
    d = date(year, 1, 4)  # Jan 4 is always in week 1 of ISO calendar
    start_of_week_1 = d - timedelta(days=d.isoweekday() - 1)

    weeks = []
    current = start_of_week_1
    while current.year <= year:
        iso_year, week_number, _ = current.isocalendar()
        if iso_year != year:
            break
        week_start = current
        week_end = current + timedelta(days=6)
        #weeks.append((week_number, week_start, week_end))
        weeks.append(week_number)
        current += timedelta(weeks=1)
    return weeks

def list_years_from2018():
    date_range = 7 
    current_year = datetime.now().year
    return list(range(2018, current_year + 15))

def get_report_week():
    today = datetime.now().today()
    week_number = today.isocalendar().week
    return week_number

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
    
        overDueActions = actionsOverDue(yyear, unit, recordType, workstream, ovrsC, ovrsH, ovrsCa)                                                              #1 of MTO Actions Overdue with summary
        actionsDueIn30Days = actionsOverDueIn30Days(yyear, unit, recordType, workstream, ovrsC, ovrsH, ovrsCa)                                                  #2 Open MTO Actions Due within 30 days
        
        threatsIn30Days = threatsDueIn30Days(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)                     #3 Threats and Opportunities Due in 30 days
        overDueThreatsOpportunity = OverDueThreatsOpportunity(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)    #4 Overdue Threats and Opportunities
        obj_top20Threats =top20ThreatsOpport(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)                     #5 Top 20 Threats & Opportunities (L3 - L5)
        threatOpportunityatL2=threatsOpportL2(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa)                    #6 Threats & Opportunities at L0 to L2
                                                                                                                                                                #7 KPI1: New Threats & Opportunity
                                                                                                                                                                #8 KPI3: Resolved Threats & Opportunity
                                                                                                                                                                #9 KPI4: Overdue Threats & Opportunity
                                                                                                                                                                #10 MTO KPI5 - Total Threats/Opportunity Score
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
                                                       'yyear':yyear, 'unit':unitName, 
                                                       'recordType':recordTypeName, 'workstream':workstreamName })

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























#============================ Junk Yard ===========================

#region 1. Planned Values
#         PlannedTW =queryTW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
#         PlannedLW=queryLW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
#         PlannedTW=round(PlannedTW/1000000, 1)
#         PlannedLW=round(PlannedLW/1000000, 1)
        
#         #2. Actuval Values (Banked YTD)
#         BankedTW = queryTW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0
#         BankedLW = queryLW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0
#         BankedTW=round(BankedTW/1000000, 1)
#         BankedLW=round(BankedLW/1000000, 1)
        
#         # region ========================== Data for the charts start from here ==============================================================
        
#         #1. Opex Funnel Chart Data
#         actual=BankedTW
#         plan=PlannedTW
        
#         #2. Banked YTD Pie Chart Data
#         chart_data=get_banked_by_function(queryTW)
#         labels = chart_data['labels']
#         data = chart_data['data']
        
#         #3 Funnel Value by Functions/Assets Dataset
#         functions_labels = list(queryTW.values_list('functions', flat=True))
#         functions_plan_data = list(queryTW.values_list('Yearly_Planned_Value', flat=True))
#         functions_actual_data = list(queryTW.values_list('Yearly_Actual_value', flat=True))
#         functions_datasets = [
#             {'label': 'Plan', 'data': functions_plan_data, 'backgroundColor': '#e0b100'},
#             {'label': 'Actual', 'data': functions_actual_data, 'backgroundColor': "#375f02"},
#         ]
        
#         #4 Initiative Movement to L3+  
#         aggregated = queryTW.filter(actual_Lgate__GateIndex__gte=3).values('functions').annotate(
#             total_value=Sum('Yearly_Planned_Value'),
#             total_count=Count('id')
#         )
        
#         movement_labels = []
#         value_to_l3 = []
#         count_to_l3 = []
        
#         for item in aggregated:
#             movement_labels.append(item['functions'] or '(Blank)')
#             value_to_l3.append(item['total_value'] or 0)
#             count_to_l3.append(item['total_count'] or 0)
        
#         #5 Total & New Initiative Count
#         initiativeCountTW = queryTW.all().values('functions').annotate(total_count=Count('id')) # This week
#         initiativeCountLW = queryLW.all().values('functions').annotate(total_count=Count('id')) # Last week
        
#         # Convert last week data to a lookup dictionary for quick access
#         last_week_dict = {item['functions']: item['total_count'] for item in initiativeCountLW}
        
#         # Prepare final merged result
#         initiative_count_labels = []
#         initiative_count_counts=[]
#         initiative_count_diffs=[]
        
#         for item in initiativeCountTW:
#             func = item['functions'] or '(Blank)'
#             count_this_week = item['total_count']
#             count_last_week = last_week_dict.get(func, 0)  # fallback to 0 if not present
#             diff = count_this_week - count_last_week
            
#             initiative_count_labels.append(func)
#             initiative_count_counts.append(count_this_week)
#             initiative_count_diffs.append(diff)

        
#         #6 Initiative Movement to L3+  
#         aggregatedLgate = queryTW.all().values('actual_Lgate').annotate(
#             total_value=Sum('Yearly_Planned_Value'),
#         )
        
#         lgateValues = []
#         lgateLabels = []
#         for item in aggregatedLgate:
#             lgateLabels.append(item['actual_Lgate'] or '(Blank)')
#             lgateValues.append(item['total_value'] or 0)
    
#         #endregion =============================================================================================================================
        
#         #3. Forecast Values
#         ForecastTW = queryTW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0
#         ForecastLW = queryLW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0
#         ForecastTW=round(ForecastTW/1000000, 1)
#         ForecastLW=round(ForecastLW/1000000, 1)
        
#         #4. Funnel Below L3
#         funnelBelowG3=queryTW.filter(actual_Lgate__GateIndex__lt=3).aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0 # Only below L3
#         if funnelBelowG3 > 0:
#             funnelBelowG3=round(PlannedTW/funnelBelowG3, 1)
#         else: 
#             funnelBelowG3=0
            
#         #5. Funnel Growth
#         FunnelGrowthTW=PlannedTW - PlannedLW
        
#         #6. Total Banked Value
#         TotalBankedTW=BankedTW - BankedLW
        
#         #6. Total Record Count
#         #totalRecordCount=queryTW.filter(condition=True).count()
#         if queryTW.exists():
#             totalRecordCount = queryTW.count()
#         else:
#             totalRecordCount = 0
        
#         #7. Top Initiatives by Value
#         topInitiatives=queryTW.order_by('-Yearly_Planned_Value')
        
#         #8. Pipeline Robustness
#         pipeLineRobustness = round(((float(PlannedTW)/50)*100)) #TODO:Note: where 50 is the value in the Opex target. Replace with {{OpexTarget}}
        
#         LastUpdated = queryTW.first().Date_Downloaded if queryTW.exists() else None
        
#         oReports = SavedFilter.objects.all()
        
#         #9. Opex Movements
#         results = opex_movements(queryLW, queryTW)
        
#         #10. Funnel Movement
#         funnel = funnel_movements(queryLW, queryTW)
        
#         #11. Opex Monthly Banking Plan
#         opex_banking_plan = opex_monthly_banking_plan(oYear)
#         opex_labels=opex_banking_plan['labels']
#         opex_plan_data=opex_banking_plan['plan_data']
#         opex_forecast_data=opex_banking_plan['forecast_data']
#         opex_actual_data=opex_banking_plan['actual_data']
        
#     except Exception as e:
#         print(traceback.format_exc())
#     return render(request, 'management/managementReport.html', {'xfunctions':oFunction, "year_range": year_range, 'oWeeks':oWeeks, 'oWeekTW':oWeekTW,
#                                                                 'record':totalRecordCount, 'FunnelSize':PlannedTW, 'ForecastYTD':ForecastTW,
#                                                                 'BankedYTD':BankedTW, 'TotalBankedTW':TotalBankedTW, 'FunnelGrowth':FunnelGrowthTW,
#                                                                 'labels': labels, 'data': data, 'funnelBelowG3':funnelBelowG3,
#                                                                 'pipeLineRobustness':pipeLineRobustness, 'oReports':oReports, 'opexRecogForm':opexRecogForm, 
#                                                                 'opexRecognition':opexRecognition, 'topInitiatives':topInitiatives, 'LastUpdated':LastUpdated,
                                                                
#                                                                 #1. Opex Funnel Chart Data
#                                                                 'actual':actual, 
#                                                                 'plan':plan,
                                                                
#                                                                 #2. Banked YTD Pie Chart Data
#                                                                 'labels': labels, 
#                                                                 'data': data, 
                                                                
#                                                                 #3 Funnel Value by Functions/Assets Dataset
#                                                                 'functions_labels':functions_labels,
#                                                                 'functions_datasets':functions_datasets,
                                                                
#                                                                 #4 Initiative Movement to L3+
#                                                                 'movement_labels': movement_labels,
#                                                                 'value_to_l3': value_to_l3,
#                                                                 'count_to_l3': count_to_l3,
                                                                
#                                                                 #5 Total & New Initiative Count
#                                                                 'initiative_count_labels':json.dumps(initiative_count_labels),
#                                                                 'initiative_count_counts':json.dumps(initiative_count_counts),
#                                                                 'initiative_count_diffs':json.dumps(initiative_count_diffs),
                                                                
#                                                                 #6 Initiative Movement to L3+  
#                                                                 'lgateValues':lgateValues,
#                                                                 'lgateLabels':lgateLabels,
                                                                
#                                                                 #9. Opex Movement
#                                                                 'opex_movement':results,
                                                                
#                                                                 #10. Funnel Movement
#                                                                 'funnel_movement':funnel,
                                                                
#                                                                 #11. Opex Monthly Banking Plan
#                                                                 'opex_labels':opex_labels,
#                                                                 'opex_plan_data':opex_plan_data,
#                                                                 'opex_forecast_data':opex_forecast_data,
#                                                                 'opex_actual_data':opex_actual_data,
#                                                             })
#

# def showLastWeek(request, oWeekLW, oYear, oWeeks, oFunction, year_range):
#     totalRecordCount=0
#     TotalBankedTW=0
#     labels=[]
#     try:
#         oUpperWeek = oWeekLW-1 # Last week / Upper Week Comparism
#         opexRecognition = opex_weekly_recognition.objects.filter(report_week=oWeekLW, Created_Date__year=oYear).first()
#         opexRecogForm = opexRecognitionForm(instance=opexRecognition)
        
#         queryTW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
#         queryLW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oUpperWeek)
        
#         #1. Planned Values
#         PlannedTW =queryTW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
#         PlannedLW=queryLW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
#         PlannedTW=round(PlannedTW/1000000, 1)
#         PlannedLW=round(PlannedLW/1000000, 1)
        
#         #2. Actuval Values (Banked YTD)
#         BankedTW = queryTW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0
#         BankedLW = queryLW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0
#         BankedTW=round(BankedTW/1000000, 1)
#         BankedLW=round(BankedLW/1000000, 1)
        
#         #region ========================== Data for the charts start from here ==============================================================
        
#         #1. Opex Funnel Chart Data
#         actual=BankedTW
#         plan=PlannedTW
        
#         #2. Banked YTD Pie Chart Data
#         chart_data=get_banked_by_function(queryTW)
#         labels = chart_data['labels']
#         data = chart_data['data']
        
#         #3 Funnel Value by Functions/Assets Dataset
#         functions_labels = list(queryTW.values_list('functions', flat=True))
#         functions_plan_data = list(queryTW.values_list('Yearly_Planned_Value', flat=True))
#         functions_actual_data = list(queryTW.values_list('Yearly_Actual_value', flat=True))
#         functions_datasets = [
#             {'label': 'Plan', 'data': functions_plan_data, 'backgroundColor': '#e0b100'},
#             {'label': 'Actual', 'data': functions_actual_data, 'backgroundColor': "#375f02"},
#         ]
        
#         #4 Initiative Movement to L3+  
#         aggregated = queryTW.filter(actual_Lgate__GateIndex__gte=3).values('functions').annotate(
#             total_value=Sum('Yearly_Planned_Value'),
#             total_count=Count('id')
#         )
        
#         movement_labels = []
#         value_to_l3 = []
#         count_to_l3 = []
        
#         for item in aggregated:
#             movement_labels.append(item['functions'] or '(Blank)')
#             value_to_l3.append(item['total_value'] or 0)
#             count_to_l3.append(item['total_count'] or 0)
        
#         #5 Total & New Initiative Count
#         initiativeCountTW = queryTW.all().values('functions').annotate(total_count=Count('id')) # This week
#         initiativeCountLW = queryLW.all().values('functions').annotate(total_count=Count('id')) # Last week
        
#         # Convert last week data to a lookup dictionary for quick access
#         last_week_dict = {item['functions']: item['total_count'] for item in initiativeCountLW}
        
#         # Prepare final merged result
#         initiative_count_labels = []
#         initiative_count_counts=[]
#         initiative_count_diffs=[]
        
#         for item in initiativeCountTW:
#             func = item['functions'] or '(Blank)'
#             count_this_week = item['total_count']
#             count_last_week = last_week_dict.get(func, 0)  # fallback to 0 if not present
#             diff = count_this_week - count_last_week
            
#             initiative_count_labels.append(func)
#             initiative_count_counts.append(count_this_week)
#             initiative_count_diffs.append(diff)

        
#         #6 Initiative Movement to L3+  
#         aggregatedLgate = queryTW.all().values('actual_Lgate').annotate(
#             total_value=Sum('Yearly_Planned_Value'),
#         )
        
#         lgateValues = []
#         lgateLabels = []
#         for item in aggregatedLgate:
#             lgateLabels.append(item['actual_Lgate'] or '(Blank)')
#             lgateValues.append(item['total_value'] or 0)
    
#         #endregion =============================================================================================================================
        
#         #3. Forecast Values
#         ForecastTW = queryTW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0
#         ForecastLW = queryLW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0
#         ForecastTW=round(ForecastTW/1000000, 1)
#         ForecastLW=round(ForecastLW/1000000, 1)
        
#         #4. Funnel Below L3
#         funnelBelowG3=queryTW.filter(actual_Lgate__GateIndex__lt=3).aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0 # Only below L3
#         if funnelBelowG3 > 0:
#             funnelBelowG3=round(PlannedTW/funnelBelowG3, 1)
#         else: 
#             funnelBelowG3=0
            
#         #5. Funnel Growth
#         FunnelGrowthTW=PlannedTW - PlannedLW
        
#         #6. Total Banked Value
#         TotalBankedTW=BankedTW - BankedLW
        
#         #6. Total Record Count
#         #totalRecordCount=queryTW.filter(condition=True).count()
#         if queryTW.exists():
#             totalRecordCount = queryTW.count()
#         else:
#             totalRecordCount = 0
        
#         #7. Top Initiatives by Value
#         topInitiatives=queryTW.order_by('-Yearly_Planned_Value')
        
#         #8. Pipeline Robustness
#         pipeLineRobustness = round((float(PlannedTW)*1.5))
        
#         LastUpdated = queryTW.first().Date_Downloaded if queryTW.exists() else None
        
#         oReports = SavedFilter.objects.all()
        
#         #9. Opex Movements
#         results = opex_movements(queryLW, queryTW)
        
#         #10. Funnel Movement
#         funnel = funnel_movements(queryLW, queryTW)
        
#         #11. Opex Monthly Banking Plan
#         opex_banking_plan = opex_monthly_banking_plan(oYear)
#         opex_labels=opex_banking_plan['labels']
#         opex_plan_data=opex_banking_plan['plan_data']
#         opex_forecast_data=opex_banking_plan['forecast_data']
#         opex_actual_data=opex_banking_plan['actual_data']
        
#     except Exception as e:
#         print(traceback.format_exc())
#     return render(request, 'management/managementReport.html', {'xfunctions':oFunction, "year_range": year_range, 'oWeeks':oWeeks, 'oWeekTW':oWeekLW, 
#                                                                 'record':totalRecordCount, 'FunnelSize':PlannedTW, 'ForecastYTD':ForecastTW,
#                                                                 'BankedYTD':BankedTW, 'TotalBankedTW':TotalBankedTW, 'FunnelGrowth':FunnelGrowthTW,
#                                                                 'funnelBelowG3':funnelBelowG3,
#                                                                 'pipeLineRobustness':pipeLineRobustness, 'oReports':oReports, 'opexRecogForm':opexRecogForm, 
#                                                                 'opexRecognition':opexRecognition, 'topInitiatives':topInitiatives, 'LastUpdated':LastUpdated,
                                                                
#                                                                 #1. Opex Funnel Chart Data
#                                                                 'actual':actual, 
#                                                                 'plan':plan,
                                                                
#                                                                 #2. Banked YTD Pie Chart Data
#                                                                 'labels': labels, 
#                                                                 'data': data, 
                                                                
#                                                                 #3 Funnel Value by Functions/Assets Dataset
#                                                                 'functions_labels':functions_labels,
#                                                                 'functions_datasets':functions_datasets,
                                                                
#                                                                 #4 Initiative Movement to L3+
#                                                                 'movement_labels': json.dumps(movement_labels),
#                                                                 'value_to_l3': json.dumps(value_to_l3),
#                                                                 'count_to_l3': json.dumps(count_to_l3),
                                                                
#                                                                 #5 Total & New Initiative Count
#                                                                 'initiative_count_labels':json.dumps(initiative_count_labels),
#                                                                 'initiative_count_counts':json.dumps(initiative_count_counts),
#                                                                 'initiative_count_diffs':json.dumps(initiative_count_diffs),
                                                                
#                                                                 #6 Initiative Movement to L3+  
#                                                                 'lgateValues':json.dumps(lgateValues),
#                                                                 'lgateLabels':json.dumps(lgateLabels),
                                                                
#                                                                 #9. Opex Movement
#                                                                 'opex_movement':results,
                                                                
#                                                                 #10. Funnel Movement
#                                                                 'funnel_movement':funnel,
                                                                
#                                                                 #11. Opex Monthly Banking Plan
#                                                                 'opex_labels':opex_labels,
#                                                                 'opex_plan_data':opex_plan_data,
#                                                                 'opex_forecast_data':opex_forecast_data,
#                                                                 'opex_actual_data':opex_actual_data,
# endregion                                                             })

#============================ Junk Yard ===========================


#region ======================= Preserved code ====================

# def OpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, opexRecogForm, opexRecognition, oWeekTWLW, oWeeks):
#     try:
#         # === Aggregates ===
#         aggregates = {
#             'planned_tw': queryTW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0,
#             'planned_lw': queryLW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0,
#             'actual_tw': queryTW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0,
#             'actual_lw': queryLW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0,
#             'forecast_tw': queryTW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0,
#             'forecast_lw': queryLW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0,
#             'below_l3': queryTW.filter(actual_Lgate__GateIndex__lt=3).aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0,
#         }

#         # Convert to millions
#         planned_tw = round(aggregates['planned_tw'] / 1_000_000, 1)
#         planned_lw = round(aggregates['planned_lw'] / 1_000_000, 1)
#         actual_tw = round(aggregates['actual_tw'] / 1_000_000, 1)
#         actual_lw = round(aggregates['actual_lw'] / 1_000_000, 1)
#         forecast_tw = round(aggregates['forecast_tw'] / 1_000_000, 1)
#         forecast_lw = round(aggregates['forecast_lw'] / 1_000_000, 1)

#         # === Chart Data ===
#         chart_data = get_banked_by_function(queryTW)
#         labels = chart_data['labels']
#         data = chart_data['data']

#         functions_labels = list(queryTW.values_list('functions', flat=True))
#         functions_datasets = [
#             {
#                 'label': 'Plan',
#                 'data': list(queryTW.values_list('Yearly_Planned_Value', flat=True)),
#                 'backgroundColor': '#e0b100',
#             },
#             {
#                 'label': 'Actual',
#                 'data': list(queryTW.values_list('Yearly_Actual_value', flat=True)),
#                 'backgroundColor': '#375f02',
#             },
#         ]

#         # === Movement to L3+ ===
#         movement_data = queryTW.filter(actual_Lgate__GateIndex__gte=3).values('functions').annotate(
#             total_value=Sum('Yearly_Planned_Value'),
#             total_count=Count('id')
#         )
#         movement_labels = [(item['functions'] or '(Blank)') for item in movement_data]
#         value_to_l3 = [item['total_value'] or 0 for item in movement_data]
#         count_to_l3 = [item['total_count'] or 0 for item in movement_data]

#         # === Initiative Count Diff ===
#         count_tw = queryTW.values('functions').annotate(total_count=Count('id'))
#         count_lw_dict = {item['functions']: item['total_count'] for item in queryLW.values('functions').annotate(total_count=Count('id'))}
#         initiative_count_labels, initiative_count_counts, initiative_count_diffs = [], [], []
#         for item in count_tw:
#             func = item['functions'] or '(Blank)'
#             tw_count = item['total_count']
#             lw_count = count_lw_dict.get(func, 0)
#             initiative_count_labels.append(func)
#             initiative_count_counts.append(tw_count)
#             initiative_count_diffs.append(tw_count - lw_count)

#         # === L-Gate Breakdown ===
#         lgate_data = queryTW.values('actual_Lgate').annotate(total_value=Sum('Yearly_Planned_Value'))
#         lgateLabels = [(item['actual_Lgate'] or '(Blank)') for item in lgate_data]
#         lgateValues = [item['total_value'] or 0 for item in lgate_data]

#         # === Derived Metrics ===
#         funnelBelowG3 = round(planned_tw / (aggregates['below_l3'] / 1_000_000), 1) if aggregates['below_l3'] else 0
#         funnelGrowthTW = planned_tw - planned_lw
#         totalBankedTW = actual_tw - actual_lw
#         totalRecordCount = queryTW.count()
#         topInitiatives = queryTW.order_by('-Yearly_Planned_Value')
#         pipeLineRobustness = round((planned_tw / 50) * 100)

#         first_row = queryTW.first()
#         lastUpdated = getattr(first_row, 'Date_Downloaded', None) if first_row else None

#         oReports = SavedFilter.objects.all()

#         # === Movement Functions ===
#         opex_movement = opex_movements(queryLW, queryTW)
#         funnel_movement = funnel_movements(queryLW, queryTW)

#         # === Monthly Banking Plan ===
#         opex_plan = opex_monthly_banking_plan(oYear)

#     except Exception as e:
#         print(traceback.format_exc())
#         # Optionally log the error
#         planned_tw = actual_tw = forecast_tw = totalBankedTW = funnelGrowthTW = funnelBelowG3 = 0
#         labels = data = functions_labels = functions_datasets = []
#         movement_labels = value_to_l3 = count_to_l3 = []
#         initiative_count_labels = initiative_count_counts = initiative_count_diffs = []
#         lgateValues = lgateLabels = []
#         topInitiatives = []
#         pipeLineRobustness = 0
#         lastUpdated = None
#         oReports = []
#         opex_movement = funnel_movement = {}
#         opex_plan = {'labels': [], 'plan_data': [], 'forecast_data': [], 'actual_data': []}
#         totalRecordCount = 0

#     return render(request, 'management/managementReport.html', {
#         'xfunctions': oFunction,
#         'year_range': year_range,
#         'oWeeks': oWeeks,
#         'oWeekTW': oWeekTWLW,
#         'record': totalRecordCount,
#         'FunnelSize': planned_tw,
#         'ForecastYTD': forecast_tw,
#         'BankedYTD': actual_tw,
#         'TotalBankedTW': totalBankedTW,
#         'FunnelGrowth': funnelGrowthTW,
#         'funnelBelowG3': funnelBelowG3,
#         'pipeLineRobustness': pipeLineRobustness,
#         'oReports': oReports,
#         'opexRecogForm': opexRecogForm,
#         'opexRecognition': opexRecognition,
#         'topInitiatives': topInitiatives,
#         'LastUpdated': lastUpdated,

#         # Charts
#         'actual': actual_tw,
#         'plan': planned_tw,
#         'labels': labels,
#         'data': data,

#         'functions_labels': functions_labels,
#         'functions_datasets': functions_datasets,

#         'movement_labels': movement_labels,
#         'value_to_l3': value_to_l3,
#         'count_to_l3': count_to_l3,

#         'initiative_count_labels': json.dumps(initiative_count_labels),
#         'initiative_count_counts': json.dumps(initiative_count_counts),
#         'initiative_count_diffs': json.dumps(initiative_count_diffs),

#         'lgateValues': lgateValues,
#         'lgateLabels': lgateLabels,

#         'opex_movement': opex_movement,
#         'funnel_movement': funnel_movement,

#         'opex_labels': opex_plan['labels'],
#         'opex_plan_data': opex_plan['plan_data'],
#         'opex_forecast_data': opex_plan['forecast_data'],
#         'opex_actual_data': opex_plan['actual_data'],
#endregion     })