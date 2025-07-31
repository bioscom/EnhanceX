from .models import *
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.db import models
from django.db.models import Q, F, Prefetch, FloatField, ExpressionWrapper
from dashboard.forms import *
import traceback
from Fit4.models import *
from reports.models import *
import pandas as pd
from django.shortcuts import render
import json
from django.db.models import Sum

from datetime import datetime, timedelta, date

from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.db.models.functions import ExtractWeek, ExtractYear
from decimal import Decimal, ROUND_HALF_UP
from django.utils.timezone import now

from django.http import JsonResponse
from django.template.loader import render_to_string

from dashboard.utilities import *
from collections import Counter, defaultdict
from django.core.serializers.json import DjangoJSONEncoder


def get_banked_by_function(queryTW):
    # Group by Function and sum Yearly_Actual_value
    labels = []
    data = []
    function_banked = queryTW.values('functions__title').annotate(total=Sum('Yearly_Actual_value')).filter(total__gt=0)
    for row in function_banked:
        label = row['functions__title'] if row and row.get('functions__title') else '(Blank)'
        labels.append(label)
        #lgateLabels.append(item['actual_Lgate'] or '(Blank)')
        value_in_millions = round((row['total'] or 0) / 1_000_000, 1)
        data.append(value_in_millions)

    context = {
        'labels': labels,
        'data': data,
    }
    return context

def add_opex_recognition(request, id=None):
    try:
        # Check if Recognition already exists for the current week
        opexRecognition = opex_weekly_recognition.objects.filter(report_week=get_report_week(), Created_Date__year=datetime.now().today().year).first()
        if opexRecognition:
            return edit_opex_recognition(request, opexRecognition.id)
        
        if request.method == "POST":
            form = opexRecognitionForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.created_by = request.user
                o.last_modified_by = request.user
                o.report_week = get_report_week()
                o.save()
                messages.success(request, '<b>Recognition added successfully.</b>')
                return redirect(reverse("dashboard:opex_report"))
        else:
            form = opexRecognitionForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_opex_recognition.html", {'opex': form})

def edit_opex_recognition(request, id):
    try:
        recogntion = get_object_or_404(opex_weekly_recognition, id=id)
        if request.method == "POST":
            form = opexRecognitionForm(data=request.POST, instance=recogntion)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()
                messages.success(request, '<b>Recognition updated successfully.</b>')
                return redirect(reverse("dashboard:opex_report"))
        else:
            form = opexRecognitionForm(instance=recogntion)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_opex_recognition.html", {'opex': form})

def add_opex_target(request, id=None):
    try:
        # Check if Recognition already exists for the current week
        opexTarget = opex_target.objects.filter(YYear=datetime.now().today().year).first()
        if opexTarget:
            return edit_opex_target(request, opexTarget.id)
        
        if request.method == "POST":
            form = opexTargetForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.created_by = request.user
                o.last_modified_by = request.user
                o.YYear = datetime.now().today().year
                o.save()
                messages.success(request, '<b>Opex Target added successfully.</b>')
                return redirect(reverse("dashboard:opex_report"))
        else:
            form = opexTargetForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_add_opex_target.html", {'opex': form})

def edit_opex_target(request, id):
    try:
        target = get_object_or_404(opex_target, id=id)
        if request.method == "POST":
            form = opexTargetForm(data=request.POST, instance=target)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()
                messages.success(request, '<b>Opex Target updated successfully.</b>')
                return redirect(reverse("dashboard:opex_report"))
        else:
            form = opexTargetForm(instance=target)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_edit_opex_target.html", {'opex': form})


#9. Opex Movements
def opex_movements(queryLW, queryTW):
    # Build dict for last week and this week keyed by (Initiative_Name, function)
    lw_dict = {
        (item.initiative_name, item.functions): item.Yearly_Actual_value or 0
        for item in queryLW
    }

    tw_dict = {
        (item.initiative_name, item.functions): item.Yearly_Actual_value or 0
        for item in queryTW
    }

    # Merge all unique keys
    all_keys = set(lw_dict.keys()).union(tw_dict.keys())
    # Build result list
    result = []
    for key in all_keys:
        last_week_val = lw_dict.get(key, 0)
        this_week_val = tw_dict.get(key, 0)
        diff = this_week_val - last_week_val

        if diff != 0:
            result.append({
                "Initiative_Name": key[0],
                "function": key[1],
                "Yearly_Actual_Last_Week": last_week_val,
                "Yearly_Actual_This_Week": this_week_val,
                "Difference": diff,
            })

    # Optional: Sort by difference descending
    result.sort(key=lambda x: x["Difference"], reverse=True)
    return result

#10. Funnel Movements
def funnel_movements(queryLW, queryTW):
    # Build dict for last week and this week keyed by (Initiative_Name, function)
    lw_dict = {
        (item.initiative_name, item.functions): item.Yearly_Planned_Value or 0
        for item in queryLW
    }

    tw_dict = {
        (item.initiative_name, item.functions): item.Yearly_Planned_Value or 0
        for item in queryTW
    }

    # Merge all unique keys
    all_keys = set(lw_dict.keys()).union(tw_dict.keys())
    # Build result list
    result = []
    for key in all_keys:
        last_week_val = lw_dict.get(key, 0)
        this_week_val = tw_dict.get(key, 0)
        diff = this_week_val - last_week_val

        if diff != 0:
            result.append({
                "Initiative_Name": key[0],
                "function": key[1],
                "Yearly_Plan_Last_Week": last_week_val,
                "Yearly_Plan_This_Week": this_week_val,
                "Difference": diff,
            })

    # Optional: Sort by difference descending
    result.sort(key=lambda x: x["Difference"], reverse=True)
    return result

#11. Monthly Banking Plan
def opex_monthly_banking_plan(selected_year):
    # Map of month names to their corresponding field prefixes
    month_fields = {
        "January": ["Jan_Plan", "Jan_Forecast", "Jan_Actual"],
        "February": ["Feb_Plan", "Feb_Forecast", "Feb_Actual"],
        "March": ["Mar_Plan", "Mar_Forecast", "Mar_Actual"],
        "April": ["Apr_Plan", "Apr_Forecast", "Apr_Actual"],
        "May": ["May_Plan", "May_Forecast", "May_Actual"],
        "June": ["Jun_Plan", "Jun_Forecast", "Jun_Actual"],
        "July": ["Jul_Plan", "Jul_Forecast", "Jul_Actual"],
        "August": ["Aug_Plan", "Aug_Forecast", "Aug_Actual"],
        "September": ["Sep_Plan", "Sep_Forecast", "Sep_Actual"],
        "October": ["Oct_Plan", "Oct_Forecast", "Oct_Actual"],
        "November": ["Nov_Plan", "Nov_Forecast", "Nov_Actual"],
        "December": ["Dec_Plan", "Dec_Forecast", "Dec_Actual"],
    }

    labels, plan_data, forecast_data, actual_data = [], [], [], []
    monthly_initiatives = defaultdict(list)  # Store initiatives per month

    # Filter records by year
    queryset = InitiativeImpact.objects.filter(
        Q(benefittype__title__icontains='Opex') | Q(benefittype__title__icontains='Other Income'),
        YYear=selected_year,
        initiative__Workstream__workstreamname__icontains='Opex',
    ).select_related("initiative").order_by("initiative__functions__title") 
    
    # Aggregate manually
    for month, fields in month_fields.items():
        month_plan_total = 0
        month_forecast_total = 0
        month_actual_total = 0

        for record in queryset:
            plan_val = getattr(record, fields[0], 0) or 0
            forecast_val = getattr(record, fields[1], 0) or 0
            actual_val = getattr(record, fields[2], 0) or 0

            if plan_val or forecast_val or actual_val:
                monthly_initiatives[month].append({
                    "functions": record.initiative.functions.title if record.initiative.functions and record.initiative.functions.title else "",
                    "initiative": str(record.initiative),
                    "slug": str(record.initiative.slug),
                    "plan": plan_val,
                    "forecast": forecast_val,
                    "actual": actual_val
                })

            month_plan_total += plan_val
            month_forecast_total += forecast_val
            month_actual_total += actual_val

        labels.append(month)
        plan_data.append(month_plan_total)
        forecast_data.append(month_forecast_total)
        actual_data.append(month_actual_total)


    # Pass to template
    context = {
        "labels": labels,
        "plan_data": plan_data,
        "forecast_data": forecast_data,
        "actual_data": actual_data,
        "monthly_initiatives": dict(monthly_initiatives),  # convert defaultdict to regular dict
    }
    
    return context

# This copies data for the week to the Model
def trigger_opex_data_copy(request):
    if request.method == "POST":
        selected_id = request.POST.get('selected_id')  # Always returns a row
        # Get current time in your timezone (e.g., Africa/Lagos)
        #now = datetime.now(pytz.timezone("Africa/Lagos"))
        now = timezone.now()
        current_week = now.isocalendar()[1]  # ISO week number (1–53)
        current_year = now.year
        
        #TODO: Uncomment the following lines if you want to restrict sync to Fridays after 9am
        # if now.weekday() != 4 or now.hour < 9:
        #     messages.error(request, "⚠️ Sync only allowed after 9am on Fridays.")
        #     return redirect('/en/opex_report')
        
        try:
            # week_number = get_report_week()
            # #today = datetime.now().today()
            # #Note Year, BenefitType and others have been selected in the filter from the report Model
            # oYear = now.year if not yyear or yyear == 'None' else yyear
            
            oFilter = SavedFilter.objects.get(id=selected_id)
            if oFilter.filter_params2 != None:
                multi_valued_keys = ['Plan_Relevance', 'Workstream', 'overall_status', 'YYear', 'benefittype', 'enabledby']
                for key in multi_valued_keys:
                    if key in oFilter.filter_params2 and isinstance(oFilter.filter_params2[key], list):
                        oFilter.filter_params2[f"{key}__in"] = oFilter.filter_params2.pop(key)
            
            query = InitiativeImpact.objects.select_related('initiative').annotate(
                    Workstream=F('initiative__Workstream'),
                    overall_status=F('initiative__overall_status'),
                    Plan_Relevance=F('initiative__Plan_Relevance'),
                    enabledby=F('initiative__enabledby'),
                    functions=F('initiative__functions')).prefetch_related('initiative__Plan_Relevance', 'initiative__enabledby').filter(**oFilter.filter_params2)
                    
            snapshots = [
                opex_weekly_Initiative_Report(
                    workstreamlead = o.initiative.workstreamlead,
                    workstreamsponsor = o.initiative.workstreamsponsor,
                    author = o.initiative.author,
                    initiative_name = o.initiative.initiative_name,
                    initiative_id = o.initiative.initiative_id,
                    Yearly_Planned_Value = o.sum_plan,
                    Yearly_Forecast_Value = o.sum_forecast,
                    Yearly_Actual_value = o.sum_actual,
                    Planned_Date = o.initiative.Planned_Date,
                    functions = o.initiative.functions,
                    slug = o.initiative.slug,
                    
                    overall_status = o.initiative.overall_status,
                    actual_Lgate = o.initiative.actual_Lgate,
                    #Plan_Relevance = o.initiative.Plan_Relevance.set(o.initiative.Plan_Relevance),
                    
                    L0_Completion_Date_Planned = o.initiative.L0_Completion_Date_Planned,
                    L1_Completion_Date_Planned = o.initiative.L1_Completion_Date_Planned,
                    L2_Completion_Date_Planned = o.initiative.L2_Completion_Date_Planned,
                    L3_Completion_Date_Planned = o.initiative.L3_Completion_Date_Planned,
                    L4_Completion_Date_Planned = o.initiative.L4_Completion_Date_Planned,
                    L5_Completion_Date_Planned = o.initiative.L5_Completion_Date_Planned,
                    Workstream = o.initiative.Workstream,
                    SavingType = o.initiative.SavingType,
                    HashTag =  o.initiative.HashTag,
                    Created_Date = o.initiative.Created_Date,
                    benefittype = o.benefittype,
                    Date_Downloaded = timezone.now(),
                    created_by = o.initiative.created_by,
                    report_week = current_week,
                )
                for o in query
            ]
            
            # Before bulk create, check if data has already been downloaded for the week

            has_this_week_data = opex_weekly_Initiative_Report.objects.annotate(week=ExtractWeek('Date_Downloaded'), year=ExtractYear('Date_Downloaded')).filter(Date_Downloaded__year=current_year, Date_Downloaded__week=current_week,)
            if has_this_week_data.exists():
                has_this_week_data.delete()
            
            # Bulk insert into the snapshot model
            opex_weekly_Initiative_Report.objects.bulk_create(snapshots)
            
            messages.success(request, "✅ Data sync completed successfully.")
        except Exception as e:
            messages.error(request, f"❌ Error during data sync: {str(e)}")
            print(traceback.format_exc(), str(e))
        return redirect('/en/opex_report')
    
def showOpexThisWeek(request, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range):
    try:
        opexRecognition = opex_weekly_recognition.objects.filter(report_week=oWeekTW, Created_Date__year=oYear).first()
        opexRecogForm = opexRecognitionForm(instance=opexRecognition)
        
        queryTW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW)
        queryLW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
    except Exception as e:
         print(traceback.format_exc())
    return OpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, opexRecogForm, opexRecognition, oWeekTW, oWeeks)

def showOpexLastWeek(request, oWeekLW, oYear, oWeeks, oFunction, year_range):
    try:
        oUpperWeek = oWeekLW-1 # Last week / Upper Week Comparism
        opexRecognition = opex_weekly_recognition.objects.filter(report_week=oWeekLW, Created_Date__year=oYear).first()
        opexRecogForm = opexRecognitionForm(instance=opexRecognition)
        
        queryTW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
        queryLW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oUpperWeek)
    except Exception as e:
         print(traceback.format_exc())
    return OpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, opexRecogForm, opexRecognition, oWeekLW, oWeeks)
   
def OpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, opexRecogForm, opexRecognition, oWeekTWLW, oWeeks):
    totalRecordCount=0
    TotalBankedTW=0
    labels=[]
    
    movement_labels = []
    value_to_l3 = []
    count_to_l3 = []
    
    initiative_count_labels = []
    initiative_count_counts=[]
    initiative_count_diffs=[]
    
    lgateValues = []
    lgateLabels = []
    
    #16. Delivery Target
    opxTargetForm = request.POST
    opexTarget = opex_target.objects.filter(YYear=oYear).first()
    if opexTarget is None:
        #Copy previous year's target to current year if it exists
        previousYearTarget = opex_target.objects.filter(YYear=oYear-1).first()
        if previousYearTarget:
            #create entry for the current year with previous year's target
            opexTarget = opex_target.objects.create(YYear=oYear, target=previousYearTarget.target)
            opxTargetForm = opexTargetForm(instance=previousYearTarget)
    else:
        opxTargetForm = opexTargetForm(instance=opexTarget)
    
    # try:
    #1. Planned Values
    PlannedTW=queryTW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
    PlannedLW=queryLW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
    PlannedTW=round(PlannedTW/1000000, 1)
    PlannedLW=round(PlannedLW/1000000, 1)
    
    #2. Actuval Values (Banked YTD)
    BankedTW = queryTW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0
    BankedLW = queryLW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0
    BankedTW=round(BankedTW/1000000, 1)
    BankedLW=round(BankedLW/1000000, 1)
    
    #3. Forecast Values
    ForecastTW = queryTW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0
    ForecastLW = queryLW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0
    ForecastTW=round(ForecastTW/1000000, 1)
    ForecastLW=round(ForecastLW/1000000, 1)
    
    #4. Funnel Below L3
    funnelBelowG3=queryTW.filter(actual_Lgate__GateIndex__lt=3).aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0 # Only below L3
    if funnelBelowG3 > 0:
        funnelBelowG3=round(funnelBelowG3/1000000, 1)
    else: 
        funnelBelowG3=0
    
    #5. Funnel Growth
    FunnelGrowthTW = (PlannedTW - PlannedLW).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    #6. Total Banked Value
    TotalBankedTW = (BankedTW - BankedLW).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    
    
    #6. Total Record Count
    #totalRecordCount=queryTW.filter(condition=True).count()
    if queryTW.exists():
        totalRecordCount = queryTW.count()
    else:
        totalRecordCount = 0
    
    #7. Top Initiatives by Value
    topInitiatives=queryTW.order_by('-Yearly_Planned_Value')
    
    opexInitiatives = queryTW.all().order_by('-Yearly_Planned_Value')
    opexTotals = opexInitiatives.aggregate(
        total_planned=Sum('Yearly_Planned_Value'),
        total_forecast=Sum('Yearly_Forecast_Value'),
        total_actual=Sum('Yearly_Actual_value')
    )
    
    #8. Pipeline Robustness
    pipeLineRobustness = round(((float(PlannedTW)/50)*100)) #TODO:Note: where 50 is the value in the Opex target. Replace with {{OpexTarget}}
    
    LastUpdated = queryTW.first().Date_Downloaded if queryTW.exists() else None
    
    oReports = SavedFilter.objects.all()
    
    #9. Opex Movements
    results = opex_movements(queryLW, queryTW)
    
    #10. Funnel Movement
    funnel = funnel_movements(queryLW, queryTW)
    
    #11. Opex Monthly Banking Plan
    opex_banking_plan = opex_monthly_banking_plan(oYear)
    opex_labels=opex_banking_plan['labels']
    opex_plan_data=opex_banking_plan['plan_data']
    opex_forecast_data=opex_banking_plan['forecast_data']
    opex_actual_data=opex_banking_plan['actual_data']
    monthly_initiatives=opex_banking_plan['monthly_initiatives']
    monthly_initiatives_json = json.dumps(monthly_initiatives, cls=DjangoJSONEncoder)
    
    #13 Initiatives Performance
    fullybankedInitiatives=queryTW.filter(
        Yearly_Actual_value__gte=F('Yearly_Planned_Value'),
        Yearly_Actual_value__gt=0,
        Yearly_Planned_Value__gt=0,
    ).annotate(achievement_pct=ExpressionWrapper(F('Yearly_Actual_value') * 100.0 / F('Yearly_Planned_Value'), output_field=FloatField())).order_by('-achievement_pct')
    
    notFullybankedInitiatives=queryTW.filter(Yearly_Actual_value__lt=F('Yearly_Planned_Value')).annotate(
        achievement_pct=ExpressionWrapper(F('Yearly_Actual_value') * 100.0 / F('Yearly_Planned_Value'), output_field=FloatField())
    ).order_by('-achievement_pct')
    
    totalFullyBanked = fullybankedInitiatives.aggregate(
        total_planned=Sum('Yearly_Planned_Value'),
        total_actual=Sum('Yearly_Actual_value')
    )
    
    totalNotFullyBanked = notFullybankedInitiatives.aggregate(
        total_planned=Sum('Yearly_Planned_Value'),
        total_actual=Sum('Yearly_Actual_value')
    )
    
    #Actual Vs Forecast Values
    fullybankedVsForecastInitiatives=queryTW.filter(
        Yearly_Actual_value__gte=F('Yearly_Forecast_Value'),
        Yearly_Actual_value__gt=0,
        Yearly_Forecast_Value__gt=0,
    ).annotate(achievement_pct=ExpressionWrapper(F('Yearly_Actual_value') * 100.0 / F('Yearly_Forecast_Value'), output_field=FloatField())).order_by('-achievement_pct')
    
    notFullybankedVsForecastInitiatives=queryTW.filter(Yearly_Actual_value__lt=F('Yearly_Forecast_Value')).annotate(
        achievement_pct=ExpressionWrapper(F('Yearly_Actual_value') * 100.0 / F('Yearly_Forecast_Value'), output_field=FloatField())
    ).order_by('-achievement_pct')
    
    totalFullyBankedVsForecast = fullybankedVsForecastInitiatives.aggregate(
        total_forecast=Sum('Yearly_Forecast_Value'),
        total_actual=Sum('Yearly_Actual_value')
    )
    
    totalNotFullyBankedVsForecast = notFullybankedVsForecastInitiatives.aggregate(
        total_forecast=Sum('Yearly_Forecast_Value'),
        total_actual=Sum('Yearly_Actual_value')
    )
    
    #region ========================== Data for the charts start from here ==============================================================
    
    #1. Opex Funnel Chart Data
    actual=BankedTW
    TotalPlan=PlannedTW
    plan=PlannedTW-BankedTW
    
    #2. Banked YTD Pie Chart Data
    chart_data=get_banked_by_function(queryTW)
    labels = chart_data['labels']
    data = chart_data['data']
    
    # #3 Funnel Value by Functions/Assets Dataset
    # functions_labels = list(queryTW.values('functions__title', flat=True))
    # functions_plan_data = list(queryTW.values_list('Yearly_Planned_Value', flat=True))
    # functions_actual_data = list(queryTW.values_list('Yearly_Actual_value', flat=True))
    # functions_datasets = [
    #     {'label': 'Plan', 'data': functions_plan_data, 'backgroundColor': '#e0b100'},
    #     {'label': 'Actual', 'data': functions_actual_data, 'backgroundColor': "#375f02"},
    # ]
    
    # ✅ Group by function title and sum values
    aggregated = (
        queryTW
        .values('functions__title')
        .annotate(
            total_plan=Sum('Yearly_Planned_Value'),
            total_actual=Sum('Yearly_Actual_value')
        )
        .order_by('-total_plan')  # Optional: for consistent label order
    )

    # ✅ Extract labels and data lists
    functions_labels = []
    functions_plan_data = []
    functions_actual_data = []

    for row in aggregated:
        functions_labels.append(row['functions__title'] or '(Blank)')
        functions_plan_data.append(round((row['total_plan'] or 0) / 1_000_000, 1))   # optional: convert to millions
        functions_actual_data.append(round((row['total_actual'] or 0) / 1_000_000, 1))

    functions_datasets = [
        {'label': 'Plan', 'data': functions_plan_data, 'backgroundColor': '#e0b100'},
        {'label': 'Actual', 'data': functions_actual_data, 'backgroundColor': "green"},
    ]
    
    #4 Initiative Movement to L3+  
    aggregated = queryTW.filter(actual_Lgate__GateIndex__gte=3).values('functions__title').annotate(
        total_value=Sum('Yearly_Planned_Value'),
        total_count=Count('id')
    )
    
    for item in aggregated:
        movement_labels.append(item['functions__title'] or '(Blank)')
        value_to_l3.append(item['total_value'] or 0)
        count_to_l3.append(item['total_count'] or 0)
    
    # Convert all Decimal values to float
    #value_to_l3_serializable = {k: str(v) if isinstance(v, Decimal) else v for k, v in value_to_l3.items()}
    
    #5 Total count, L3+ & New Initiative per workstream
    initiativeCountTW = queryTW.all().values('functions__title').annotate(total_count=Count('id')) # This week
    initiativeCountLW = queryLW.all().values('functions__title').annotate(total_count=Count('id')) # Last week
    
    # Convert last week data to a lookup dictionary for quick access
    last_week_dict = {item['functions__title']: item['total_count'] for item in initiativeCountLW}
    
    # Prepare final merged result
    
    
    for item in initiativeCountTW:
        func = item['functions__title'] or '(Blank)'
        count_this_week = item['total_count']
        count_last_week = last_week_dict.get(func, 0)  # fallback to 0 if not present
        diff = count_this_week - count_last_week
        
        initiative_count_labels.append(func)
        initiative_count_counts.append(count_this_week)
        initiative_count_diffs.append(diff)

    
    #6 Initiative Movement to L3+  
    aggregatedLgate = queryTW.all().values('actual_Lgate__LGate').annotate(
        total_value=Sum('Yearly_Planned_Value'),
    )
    
    for item in aggregatedLgate:
        lgateLabels.append(item['actual_Lgate__LGate'] or '(Blank)')
        lgateValues.append(round((item['total_value'] or 0) / 1_000_000, 1))
        #functions_actual_data.append(round((row['total_actual'] or 0) / 1_000_000, 1))

    #endregion =============================================================================================================================
         
    # except Exception as e:
    #     print(traceback.format_exc())
    return render(request, 'management/opex/opex.html', {'xfunctions':oFunction, 
                                                         "year_range": year_range, 
                                                         'oWeeks':oWeeks, 
                                                         'oWeekTW':oWeekTWLW,
                                                        'record':totalRecordCount, 
                                                        'FunnelSize':PlannedTW, 
                                                        'ForecastYTD':ForecastTW,
                                                        'BankedYTD':BankedTW, 
                                                        'TotalBankedTW':TotalBankedTW, 
                                                        'FunnelGrowth':FunnelGrowthTW,
                                                        'funnelBelowG3':funnelBelowG3,
                                                        'pipeLineRobustness':pipeLineRobustness, 
                                                        'oReports':oReports, 'opexRecogForm':opexRecogForm, 
                                                        'opexRecognition':opexRecognition, 
                                                        'topInitiatives':topInitiatives, 
                                                        'LastUpdated':LastUpdated,
                                                        'oYear':oYear,

                                                        #1. Opex Funnel Chart Data
                                                        'actual':actual, 
                                                        'plan':plan,
                                                        
                                                        #2. Banked YTD Pie Chart Data
                                                        'labels': labels, 
                                                        'data': json.dumps(data, default=str), 
                                                        
                                                        #3 Funnel Value by Functions/Assets Dataset
                                                        'functions_labels':json.dumps(functions_labels, default=str),
                                                        'functions_datasets':json.dumps(functions_datasets, default=str),
                                                        
                                                        #4 Initiative Movement to L3+
                                                        'movement_labels': json.dumps(movement_labels), #movement_label
                                                        'value_to_l3': json.dumps(value_to_l3, default=str),
                                                        'count_to_l3': json.dumps(count_to_l3),
                                                        
                                                        #5 Total & New Initiative Count
                                                        'initiative_count_labels':json.dumps(initiative_count_labels),
                                                        'initiative_count_counts':json.dumps(initiative_count_counts),
                                                        'initiative_count_diffs':json.dumps(initiative_count_diffs),
                                                        
                                                        #6 Initiative Movement to L3+  
                                                        'lgateValues':json.dumps(lgateValues, default=str),
                                                        'lgateLabels':lgateLabels,
                                                        
                                                        #9. Opex Movement
                                                        'opex_movement':results,
                                                        
                                                        #10. Funnel Movement
                                                        'funnel_movement':funnel,
                                                        
                                                        #11. Opex Monthly Banking Plan
                                                        'opex_labels':opex_labels,
                                                        'opex_plan_data':json.dumps(opex_plan_data, default=str),
                                                        'opex_forecast_data':json.dumps(opex_forecast_data, default=str),
                                                        'opex_actual_data':json.dumps(opex_actual_data, default=str),
                                                        'monthly_initiatives':monthly_initiatives,
                                                        'monthly_initiatives_json':monthly_initiatives_json,
                                                        
                                                        'opexInitiatives':opexInitiatives,
                                                        'opex_total_planned': opexTotals['total_planned'] or 0,
                                                        'opex_total_forecast': opexTotals['total_forecast'] or 0,
                                                        'opex_total_actual': opexTotals['total_actual'] or 0,
                                                        
                                                        #13 Initiatives Performance
                                                        #Actual Vs Plan
                                                        'fullybankedInitiatives':fullybankedInitiatives,
                                                        'fullybanked_total_planned': totalFullyBanked['total_planned'] or 0,
                                                        'fullybanked_total_actual': totalFullyBanked['total_actual'] or 0,
                                                        
                                                        'notFullybankedInitiatives':notFullybankedInitiatives,
                                                        'notFullybanked_total_planned': totalNotFullyBanked['total_planned'] or 0,
                                                        'notFullybanked_total_actual': totalNotFullyBanked['total_actual'] or 0,
                                                        
                                                        #Actual Vs Forecast
                                                        'fullybankedVsForecastInitiatives':fullybankedVsForecastInitiatives,
                                                        'fullybanked_total_forecast': totalFullyBankedVsForecast['total_forecast'] or 0,
                                                        'fullybankedVsForecast_total_actual': totalFullyBankedVsForecast['total_actual'] or 0,
                                                        
                                                        'notFullybankedVsForecastInitiatives':notFullybankedVsForecastInitiatives,
                                                        'notFullybanked_total_forecast': totalNotFullyBankedVsForecast['total_forecast'] or 0,
                                                        'notFullybankedVsForecast_total_actual': totalNotFullyBankedVsForecast['total_actual'] or 0,
                                                                
                                                        'opexTarget': opexTarget,
                                                        'opxTargetForm': opxTargetForm,
                                                    })

def ajax_show_opex_last_week(request):
    #if request.is_ajax() and request.method == "GET":
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        try:
            oWeek = int(request.GET.get("week"))
            oWeekLW = oWeek - 1  # Last week
            oYear = int(request.GET.get("year"))
            oFunction = request.user.profile.function if hasattr(request.user, 'profile') else None
            year_range = list_years_from2018() #list(range(oYear - 1, oYear + 2))  # or use your existing logic

            # load your queryTW, queryLW, deliveryRecogForm etc here (reuse your existing logic)
            opexRecognition = opex_weekly_recognition.objects.filter(report_week=oWeekLW, Created_Date__year=oYear).first()
            opexRecogForm = opexRecognitionForm(instance=opexRecognition)
            
            queryTW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeek)
            queryLW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
        
            context = ajaxOpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, opexRecogForm, opexRecognition, oWeek, get_weeks_in_year(oYear))  # reuse existing logic

            html = render_to_string("management/opex/ajax_partial.html", context, request=request)
            
            return JsonResponse({'success': True, 'html': html})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

def ajaxOpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, opexRecogForm, opexRecognition, oWeekTWLW, oWeeks):
    totalRecordCount=0
    TotalBankedTW=0
    labels=[]
    
    movement_labels = []
    value_to_l3 = []
    count_to_l3 = []
    
    initiative_count_labels = []
    initiative_count_counts=[]
    initiative_count_diffs=[]
    
    lgateValues = []
    lgateLabels = []
    
    #16. Delivery Target
    opxTargetForm = request.POST
    opexTarget = opex_target.objects.filter(YYear=oYear).first()
    if opexTarget is None:
        #Copy previous year's target to current year if it exists
        previousYearTarget = opex_target.objects.filter(YYear=oYear-1).first()
        if previousYearTarget:
            #create entry for the current year with previous year's target
            opexTarget = opex_target.objects.create(YYear=oYear, target=previousYearTarget.target)
            opxTargetForm = opexTargetForm(instance=previousYearTarget)
    else:
        opxTargetForm = opexTargetForm(instance=opexTarget)

    try:
        #1. Planned Values
        PlannedTW=queryTW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
        PlannedLW=queryLW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
        PlannedTW=round(PlannedTW/1000000, 1)
        PlannedLW=round(PlannedLW/1000000, 1)
        
        #2. Actuval Values (Banked YTD)
        BankedTW = queryTW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0
        BankedLW = queryLW.aggregate(total=Sum('Yearly_Actual_value'))['total'] or 0
        BankedTW=round(BankedTW/1000000, 1)
        BankedLW=round(BankedLW/1000000, 1)
        
        #3. Forecast Values
        ForecastTW = queryTW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0
        ForecastLW = queryLW.aggregate(total=Sum('Yearly_Forecast_Value'))['total'] or 0
        ForecastTW=round(ForecastTW/1000000, 1)
        ForecastLW=round(ForecastLW/1000000, 1)
        
        #4. Funnel Below L3
        funnelBelowG3=queryTW.filter(actual_Lgate__GateIndex__lt=3).aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0 # Only below L3
        if funnelBelowG3 > 0:
            funnelBelowG3=round(funnelBelowG3/1000000, 1)
        else: 
            funnelBelowG3=0
        
        #5. Funnel Growth
        FunnelGrowthTW = round(float(PlannedTW) - float(PlannedLW), 1) #(PlannedTW - PlannedLW).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    
        #6. Total Banked Value
        TotalBankedTW = round(float(BankedTW) - float(BankedLW), 1) #(BankedTW - BankedLW).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


        #6. Total Record Count
        #totalRecordCount=queryTW.filter(condition=True).count()
        if queryTW.exists():
            totalRecordCount = queryTW.count()
        else:
            totalRecordCount = 0
        
        #7. Top Initiatives by Value
        topInitiatives=queryTW.order_by('-Yearly_Planned_Value')
        # Detect duplicates by initiative name
        names = [item.initiative_name for item in topInitiatives]
        duplicates = {name for name, count in Counter(names).items() if count > 1}
        
        #8. Pipeline Robustness
        pipeLineRobustness = round(((float(PlannedTW)/50)*100)) #TODO:Note: where 50 is the value in the Opex target. Replace with {{OpexTarget}}
        
        LastUpdated = queryTW.first().Date_Downloaded if queryTW.exists() else None
        
        oReports = SavedFilter.objects.all()
        
        #9. Opex Movements
        results = opex_movements(queryLW, queryTW)
        
        #10. Funnel Movement
        funnel = funnel_movements(queryLW, queryTW)
        
        #11. Opex Monthly Banking Plan
        opex_banking_plan = opex_monthly_banking_plan(oYear)
        opex_labels=opex_banking_plan['labels']
        opex_plan_data=opex_banking_plan['plan_data']
        opex_forecast_data=opex_banking_plan['forecast_data']
        opex_actual_data=opex_banking_plan['actual_data']
        
        #13 Initiatives Performance
        fullybankedInitiatives=queryTW.filter(
            Yearly_Actual_value__gte=F('Yearly_Planned_Value'),
            Yearly_Actual_value__gt=0,
            Yearly_Planned_Value__gt=0,
        ).annotate(achievement_pct=ExpressionWrapper(F('Yearly_Actual_value') * 100.0 / F('Yearly_Planned_Value'), output_field=FloatField())).order_by('-achievement_pct')
        
        notFullybankedInitiatives=queryTW.filter(Yearly_Actual_value__lt=F('Yearly_Planned_Value')).annotate(
            achievement_pct=ExpressionWrapper(F('Yearly_Actual_value') * 100.0 / F('Yearly_Planned_Value'), output_field=FloatField())
        ).order_by('-achievement_pct')
        
        #region ========================== Data for the charts start from here ==============================================================
        
        #1. Opex Funnel Chart Data
        actual=BankedTW
        TotalPlan=PlannedTW
        plan=PlannedTW-BankedTW
        
        #2. Banked YTD Pie Chart Data
        chart_data=get_banked_by_function(queryTW)
        labels = chart_data['labels']
        data = chart_data['data']
        
        # #3 Funnel Value by Functions/Assets Dataset
        # functions_labels = list(queryTW.values('functions__title', flat=True))
        # functions_plan_data = list(queryTW.values_list('Yearly_Planned_Value', flat=True))
        # functions_actual_data = list(queryTW.values_list('Yearly_Actual_value', flat=True))
        # functions_datasets = [
        #     {'label': 'Plan', 'data': functions_plan_data, 'backgroundColor': '#e0b100'},
        #     {'label': 'Actual', 'data': functions_actual_data, 'backgroundColor': "#375f02"},
        # ]
        
        # ✅ Group by function title and sum values
        aggregated = (
            queryTW
            .values('functions__title')
            .annotate(
                total_plan=Sum('Yearly_Planned_Value'),
                total_actual=Sum('Yearly_Actual_value')
            )
            .order_by('-total_plan')  # Optional: for consistent label order
        )

        # ✅ Extract labels and data lists
        functions_labels = []
        functions_plan_data = []
        functions_actual_data = []

        for row in aggregated:
            functions_labels.append(row['functions__title'] or '(Blank)')
            functions_plan_data.append(round((row['total_plan'] or 0) / 1_000_000, 1))   # optional: convert to millions
            functions_actual_data.append(round((row['total_actual'] or 0) / 1_000_000, 1))

        functions_datasets = [
            {'label': 'Plan', 'data': functions_plan_data, 'backgroundColor': '#e0b100'},
            {'label': 'Actual', 'data': functions_actual_data, 'backgroundColor': "green"},
        ]
        
        #4 Initiative Movement to L3+  
        aggregated = queryTW.filter(actual_Lgate__GateIndex__gte=3).values('functions__title').annotate(
            total_value=Sum('Yearly_Planned_Value'),
            total_count=Count('id')
        )
        
        for item in aggregated:
            movement_labels.append(item['functions__title'] or '(Blank)')
            value_to_l3.append(item['total_value'] or 0)
            count_to_l3.append(item['total_count'] or 0)
        
        # Convert all Decimal values to float
        #value_to_l3_serializable = {k: str(v) if isinstance(v, Decimal) else v for k, v in value_to_l3.items()}
        
        #5 Total & New Initiative Count
        initiativeCountTW = queryTW.all().values('functions__title').annotate(total_count=Count('id')) # This week
        initiativeCountLW = queryLW.all().values('functions__title').annotate(total_count=Count('id')) # Last week
        
        # Convert last week data to a lookup dictionary for quick access
        last_week_dict = {item['functions__title']: item['total_count'] for item in initiativeCountLW}
        
        # Prepare final merged result
        
        
        for item in initiativeCountTW:
            func = item['functions__title'] or '(Blank)'
            count_this_week = item['total_count']
            count_last_week = last_week_dict.get(func, 0)  # fallback to 0 if not present
            diff = count_this_week - count_last_week
            
            initiative_count_labels.append(func)
            initiative_count_counts.append(count_this_week)
            initiative_count_diffs.append(diff)

        
        #6 Initiative Movement to L3+  
        aggregatedLgate = queryTW.all().values('actual_Lgate__LGate').annotate(
            total_value=Sum('Yearly_Planned_Value'),
        )
        
        for item in aggregatedLgate:
            lgateLabels.append(item['actual_Lgate__LGate'] or '(Blank)')
            lgateValues.append(round((item['total_value'] or 0) / 1_000_000, 1))
            #functions_actual_data.append(round((row['total_actual'] or 0) / 1_000_000, 1))
    
        #endregion =============================================================================================================================
         
    except Exception as e:
        print(traceback.format_exc())
    return {'xfunctions':oFunction, "year_range": year_range, 'oWeeks':oWeeks, 'oWeekTW':oWeekTWLW,
            'record':totalRecordCount, 'FunnelSize':PlannedTW, 'ForecastYTD':ForecastTW,
            'BankedYTD':BankedTW, 'TotalBankedTW':TotalBankedTW, 'FunnelGrowth':FunnelGrowthTW,
            'funnelBelowG3':funnelBelowG3,
            'pipeLineRobustness':pipeLineRobustness, 'oReports':oReports, 'opexRecogForm':opexRecogForm, 
            'opexRecognition':opexRecognition, 'topInitiatives':topInitiatives, 'duplicates':duplicates, 'LastUpdated':LastUpdated,
            
            #1. Opex Funnel Chart Data
            'actual':actual, 
            'plan':plan,
                                                                
            #2. Banked YTD Pie Chart Data
            'labels': labels, 
            'data': json.dumps(data, default=str), 
                                                                
            #3 Funnel Value by Functions/Assets Dataset
            'functions_labels':json.dumps(functions_labels, default=str),
            'functions_datasets':json.dumps(functions_datasets, default=str),
            
            #4 Initiative Movement to L3+
            'movement_labels': json.dumps(movement_labels), #movement_label
            'value_to_l3': json.dumps(value_to_l3, default=str),
            'count_to_l3': json.dumps(count_to_l3),
            
            #5 Total & New Initiative Count
            'initiative_count_labels':json.dumps(initiative_count_labels),
            'initiative_count_counts':json.dumps(initiative_count_counts),
            'initiative_count_diffs':json.dumps(initiative_count_diffs),
            
            #6 Initiative Movement to L3+  
            'lgateValues':json.dumps(lgateValues, default=str),
            'lgateLabels':lgateLabels,
            
            #9. Opex Movement
            'opex_movement':results,
            
            #10. Funnel Movement
            'funnel_movement':funnel,
            
            #11. Opex Monthly Banking Plan
            'opex_labels':opex_labels,
            'opex_plan_data':json.dumps(opex_plan_data, default=str),
            'opex_forecast_data':json.dumps(opex_forecast_data, default=str),
            'opex_actual_data':json.dumps(opex_actual_data, default=str),
            
            #13 Initiatives Performance
            'fullybankedInitiatives':fullybankedInitiatives,
            'notFullybankedInitiatives':notFullybankedInitiatives,
            
            'opexTarget': opexTarget,
            'opxTargetForm': opxTargetForm,
        }
    
    
def delete_opex_duplicate(request, id):
    initiative = get_object_or_404(opex_weekly_Initiative_Report, id=id)
    initiative.delete()
    return redirect(reverse("dashboard:opex_report"))
    #return redirect(request.META.get('HTTP_REFERER', 'your-fallback-url'))