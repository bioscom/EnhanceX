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
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum

from datetime import datetime, timedelta, date

from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.db.models.functions import ExtractWeek, ExtractYear
from decimal import Decimal, ROUND_HALF_UP
from django.utils.timezone import now

from dashboard.utilities import *
from collections import defaultdict


def get_banked_by_function(queryTW):
    # Group by Function and sum Yearly_Actual_value
    labels = []
    data = []
    function_banked = queryTW.values('Workstream__workstreamname').annotate(total=Sum('Yearly_Actual_value')).filter(total__gt=0)
    for row in function_banked:
        raw_name = row['Workstream__workstreamname'] if row and row.get('Workstream__workstreamname') else '(Blank)'
        clean_name = raw_name.replace("Renaissance Delivery - ", "")
        
        #label = row['Workstream__workstreamname'] if row and row.get('Workstream__workstreamname') else '(Blank)'
        labels.append(clean_name)
        #lgateLabels.append(item['actual_Lgate'] or '(Blank)')
        value_in_millions = round((row['total'] or 0) / 1_000_000, 1)
        data.append(value_in_millions)

    context = {
        'labels': labels,
        'data': data,
    }
    return context

def upload_weekly_commitment_excel(request):
    if request.method == 'POST':

        has_this_week_data = weekly_commitment_report.objects.annotate(week=ExtractWeek('date_downloaded'), year=ExtractYear('date_downloaded')).filter(date_downloaded__year=now().year, date_downloaded__week=get_report_week())
        if has_this_week_data.exists():
            has_this_week_data.delete()
        
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file)

                # Optional: Check required columns
                required_columns = ['functions', 'initiative', 'commitments', 'status']
                df.columns = [col.strip().lower() for col in df.columns]  # normalize
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, "Excel sheet is missing required columns.")
                    return redirect(reverse("dashboard:delivery_report"))

                for _, row in df.iterrows():
                    weekly_commitment_report.objects.create(
                        functions=row['functions'],
                        initiative=row['initiative'],
                        commitments=row.get('commitments', ''),
                        status=bool(row['status']),
                        report_week=get_report_week(),
                        report_year=now().year,
                        created_by=request.user
                    )

                messages.success(request, "Excel data uploaded successfully.")
                return redirect(reverse("dashboard:delivery_report"))
            except Exception as e:
                messages.error(request, f"Upload failed: {str(e)}")
                print(traceback.format_exc(), str(e))
    else:
        form = ExcelUploadForm()
    return redirect(reverse("dashboard:delivery_report"))

def add_delivery_recognition(request, id=None):
    try:
        # Check if Recognition already exists for the current week
        deliveryRecognition = delivery_weekly_recognition.objects.filter(report_week=get_report_week(), Created_Date__year=datetime.now().today().year).first()
        if deliveryRecognition:
            return edit_delivery_recognition(request, deliveryRecognition.id)
        
        if request.method == "POST":
            form = deliveryRecognitionForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.created_by = request.user
                o.last_modified_by = request.user
                o.report_week = get_report_week()
                o.save()
                messages.success(request, '<b>Recognition added successfully.</b>')
                return redirect(reverse("dashboard:delivery_report"))
        else:
            form = deliveryRecognitionForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_add_delivery_recognition.html", {'opex': form})

def edit_delivery_recognition(request, id):
    try:
        recogntion = get_object_or_404(delivery_weekly_recognition, id=id)
        if request.method == "POST":
            form = deliveryRecognitionForm(data=request.POST, instance=recogntion)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()
                messages.success(request, '<b>Recognition updated successfully.</b>')
                return redirect(reverse("dashboard:delivery_report"))
        else:
            form = deliveryRecognitionForm(instance=recogntion)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_edit_delivery_recognition.html", {'opex': form})

#9. Delivery Movements
def delivery_movements(queryLW, queryTW):
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
def delivery_monthly_banking_plan_Old(selected_year):
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

    # Filter records by year
    queryset = InitiativeImpact.objects.filter(
        YYear=selected_year,
        initiative__Workstream__workstreamname__icontains='Renaissance Delivery'
    )
    
    # Aggregate manually
    for month, fields in month_fields.items():
        agg = queryset.aggregate(
            plan=Sum(fields[0]),
            forecast=Sum(fields[1]),
            actual=Sum(fields[2])
        )

        labels.append(month)
        plan_data.append(agg["plan"] or 0)
        forecast_data.append(agg["forecast"] or 0)
        actual_data.append(agg["actual"] or 0)

    # Pass to template
    context = {
        "labels": labels,
        "plan_data": plan_data,
        "forecast_data": forecast_data,
        "actual_data": actual_data,
    }
    
    return context

def delivery_monthly_banking_plan(selected_year):
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

    queryset = InitiativeImpact.objects.filter(
        YYear=selected_year,
        initiative__Workstream__workstreamname__icontains='Renaissance Delivery',
        benefittype__title__icontains='FCF'
    ).select_related("initiative").order_by("initiative__Workstream__workstreamname")

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
                    "workstream": str(record.initiative.Workstream.workstreamname).replace("Renaissance Delivery - ", ""),
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

    context = {
        "labels": labels,
        "plan_data": plan_data,
        "forecast_data": forecast_data,
        "actual_data": actual_data,
        "monthly_initiatives": dict(monthly_initiatives),  # convert defaultdict to regular dict
    }

    return context

# This copies data for the week to the Model
def trigger_delivery_data_copy(request):
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
        #     return redirect('/en/delivery_report')
        
        try:
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
                delivery_weekly_Initiative_Report(
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
            
            # Before bulk create, check if data has already been downloaded for the week. If loaded, delete and reload again
            has_this_week_data = delivery_weekly_Initiative_Report.objects.annotate(week=ExtractWeek('Date_Downloaded'), year=ExtractYear('Date_Downloaded')).filter(Date_Downloaded__year=current_year, Date_Downloaded__week=current_week,)
            if has_this_week_data.exists():
                has_this_week_data.delete()
            
            # Bulk insert into the snapshot model
            delivery_weekly_Initiative_Report.objects.bulk_create(snapshots)
            
            messages.success(request, "✅ Data sync completed successfully.")
        except Exception as e:
            messages.error(request, f"❌ Error during data sync: {str(e)}")
            print(traceback.format_exc(), str(e))
        return redirect('/en/delivery_report')

def showDeliveryThisWeek(request, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range):
    try:
        deliveryRecognition = delivery_weekly_recognition.objects.filter(report_week=oWeekTW, Created_Date__year=oYear).first()
        deliveryRecogForm = deliveryRecognitionForm(instance=deliveryRecognition)
        
        queryTW = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW)
        queryLW = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
    except Exception as e:
         print(traceback.format_exc())
    return DeliveryPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, deliveryRecogForm, deliveryRecognition, oWeekTW, oWeeks)

def showDeliveryLastWeek(request, oWeekLW, oYear, oWeeks, oFunction, year_range):
    try:
        oUpperWeek = oWeekLW-1 # Last week / Upper Week Comparism
        deliveryRecognition = delivery_weekly_recognition.objects.filter(report_week=oWeekLW, Created_Date__year=oYear).first()
        deliveryRecogForm = deliveryRecognitionForm(instance=deliveryRecognition)
        
        queryTW = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
        queryLW = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oUpperWeek)
    except Exception as e:
         print(traceback.format_exc())
    return DeliveryPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, deliveryRecogForm, deliveryRecognition, oWeekLW, oWeeks)

def DeliveryPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, deliveryRecogForm, deliveryRecognition, oWeekTWLW, oWeeks):  
    movement_labels = []
    value_to_l3 = []
    count_to_l3 = []
    
    initiative_count_labels = []
    initiative_count_counts=[]
    initiative_count_diffs=[]
    initiative_count_L3plus = []
    
    lgateValues = []
    lgateLabels = []
    
    #region ====================  Dashboard Data Points =====================================
    #try:
    #1. Planned Values
    PlannedTW=queryTW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
    PlannedLW=queryLW.aggregate(total=Sum('Yearly_Planned_Value'))['total'] or 0
    PlannedTW=round(PlannedTW/1000000, 1)
    PlannedLW=round(PlannedLW/1000000, 1)
    
    #2. Actual Values (Banked YTD)
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
    
    if queryTW.exists():
        totalRecordCount = queryTW.count()
    else:
        totalRecordCount = 0
    
    #7. Top Initiatives by Value (This just orders list by Planned value, it may be required to show just top 10 :[10])
    topInitiatives=queryTW.order_by('-Yearly_Planned_Value')
    
    #8. Pipeline Robustness
    pipeLineRobustness = round(((float(PlannedTW)/100)*100)) #TODO:Note: where 100 is the value in the Delivery target. Replace with {{OpexTarget}}
    
    LastUpdated = queryTW.first().Date_Downloaded if queryTW.exists() else None
    
    oReports = SavedFilter.objects.all()
    
    #9. Delivery Movements
    bankedThisWeek = delivery_movements(queryLW, queryTW)
    
    #10. Funnel Movement
    funnelChangeThisWeek = funnel_movements(queryLW, queryTW)
    
    #11. Delivery Monthly Banking Plan
    delivery_banking_plan = delivery_monthly_banking_plan(oYear)
    delivery_labels=delivery_banking_plan['labels']
    delivery_plan_data=delivery_banking_plan['plan_data']
    delivery_forecast_data=delivery_banking_plan['forecast_data']
    delivery_actual_data=delivery_banking_plan['actual_data']
    monthly_initiatives=delivery_banking_plan['monthly_initiatives']
    monthly_initiatives_json = json.dumps(monthly_initiatives, cls=DjangoJSONEncoder)
    
    #14. Lists of Initiatives from East, West and NOV that plotted the monthly Banking Plan
    eastAssetInitiatives = queryTW.filter(Workstream__workstreamname__icontains='East').order_by('-Yearly_Planned_Value')
    eastAssetTotals = eastAssetInitiatives.aggregate(
        total_planned=Sum('Yearly_Planned_Value'),
        total_actual=Sum('Yearly_Actual_value')
    )
    
    westAssetInitiatives = queryTW.filter(Workstream__workstreamname__icontains='West').order_by('-Yearly_Planned_Value')
    westAssetTotals = westAssetInitiatives.aggregate(
        total_planned=Sum('Yearly_Planned_Value'),
        total_actual=Sum('Yearly_Actual_value')
    )
    
    novAssetInitiatives = queryTW.filter(Workstream__workstreamname__icontains='NOV').order_by('-Yearly_Planned_Value')
    novAssetTotals = novAssetInitiatives.aggregate(
        total_planned=Sum('Yearly_Planned_Value'),
        total_actual=Sum('Yearly_Actual_value')
    )
    
    
    
    #13 Initiatives Performance
    #Actual Vs Planned Values
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
    
    
    
    #15. Upload Commitment Report
    formUploadWeeklyCommitments = ExcelUploadForm(request.POST) #upload_weekly_commitment_excel(request)
    weeklyCommitments = weekly_commitment_report.objects.filter(report_week=oWeekTWLW, date_downloaded__year=oYear)
    #deliveryRecogForm = deliveryRecognitionForm(instance=deliveryRecognition)
    #endregion ====================  Dashboard Data Points =====================================
    
    #region ========================== Data for the charts start from here ==============================================================
    
    #region 1. Opex Funnel Chart Data
    actual=BankedTW
    TotalPlan=PlannedTW
    plan=PlannedTW-BankedTW
    #endregion
    
    #region 2. Banked YTD (Pie Chart Data)
    chart_data=get_banked_by_function(queryTW)
    labels = chart_data['labels']
    data = chart_data['data']
    #endregion
    
    #region 3. Funnel Value by Workstream  
    # Group by workstream workstreamname and sum values
    aggregated = (queryTW.values('Workstream__workstreamname')
        .annotate(total_plan=Sum('Yearly_Planned_Value'), total_actual=Sum('Yearly_Actual_value')).order_by('-total_plan'))

    # ✅ Extract labels and data lists
    functions_labels = []
    functions_plan_data = []
    functions_actual_data = []

    for row in aggregated:
        raw_name = row['Workstream__workstreamname'] or '(Blank)'
        clean_name = raw_name.replace("Renaissance Delivery - ", "")
        functions_labels.append(clean_name)
       # functions_labels.append(row['Workstream__workstreamname'] or '(Blank)')
        functions_plan_data.append(round((row['total_plan'] or 0) / 1_000_000, 1))   # optional: convert to millions
        functions_actual_data.append(round((row['total_actual'] or 0) / 1_000_000, 1))

    functions_datasets = [
        {'label': 'Plan', 'data': functions_plan_data, 'backgroundColor': '#e0b100'},
        {'label': 'Actual', 'data': functions_actual_data, 'backgroundColor': "green"},
    ]
    
    line_data = {
        "label": "Target Line",
        "data": [40, 55, 5],  # should match length of labels
        "type": "line",
        "borderColor": "red",
        "borderWidth": 2,
        "fill": False,
        "tension": 0.1,  # smooth curve (optional)
        "pointBackgroundColor": "red",
        "pointRadius": 3,
        "borderDash": [5, 5] 
    }
    
    functions_datasets.append(line_data)  # Add target line to datasets
    #endregion
    
    #region 4 Initiative Movement to L3+ by Value & Count  
    aggregated_TW = queryTW.filter(actual_Lgate__GateIndex__gte=3).values('Workstream__workstreamname').annotate(
        total_value=Sum('Yearly_Planned_Value'), total_count=Count('id')).order_by('-total_value')
    
    aggregated_LW = queryLW.filter(actual_Lgate__GateIndex__gte=3).values('Workstream__workstreamname').annotate(
        total_value=Sum('Yearly_Planned_Value'), total_count=Count('id')).order_by('-total_value')
    
    # Convert to dicts for easy lookup
    last_week_dict = {item['Workstream__workstreamname']: item for item in aggregated_LW}
    this_week_dict = {item['Workstream__workstreamname']: item for item in aggregated_TW}

    all_keys = set(this_week_dict.keys()) | set(last_week_dict.keys())
    
    for workstream in all_keys:
        this_item = this_week_dict.get(workstream, {'total_value': 0, 'total_count': 0})
        last_item = last_week_dict.get(workstream, {'total_value': 0, 'total_count': 0})

        diff_value = (this_item['total_value'] or 0) - (last_item['total_value'] or 0)
        diff_count = (this_item['total_count'] or 0) - (last_item['total_count'] or 0)
        
        #raw_name = item['Workstream__workstreamname'] or '(Blank)'
        clean_name = (workstream or '(Blank)').replace("Renaissance Delivery - ", "")
        movement_labels.append(clean_name)
        value_to_l3.append(diff_value)
        count_to_l3.append(diff_count)
    #endregion 
    
    #region 5 Total count, L3+ & New Initiative per workstream
    initiativeCountTW = queryTW.all().values('Workstream__workstreamname').annotate(total_count=Count('id')) # This week
    initiativeCountTWL3 = queryTW.filter(actual_Lgate__GateIndex__gte=3).values('Workstream__workstreamname').annotate(l3_count=Count('id')) # Initiative Count at L3+
    initiativeCountLW = queryLW.all().values('Workstream__workstreamname').annotate(total_count=Count('id')) # Last week
    
    # Step 2: Convert last week and L3+ counts to dictionaries
    # Normalize workstream names to cleaned names
    def clean_name(name):
        return (name or '(Blank)').replace("Renaissance Delivery - ", "")

    # Lookup tables for quick merge
    last_week_dict = {
        clean_name(item['Workstream__workstreamname']): item['total_count']
        for item in initiativeCountLW
    }
    
    l3_count_dict = {
        clean_name(item['Workstream__workstreamname']): item['l3_count']
        for item in initiativeCountTWL3
    }
    
    # Prepare final merged result
    for item in initiativeCountTW:
        raw_name = item['Workstream__workstreamname']
        cleaned = clean_name(raw_name)
        
        count_this_week = item['total_count']
        count_last_week = last_week_dict.get(cleaned, 0)  # fallback to 0 if not present
        count_l3 = l3_count_dict.get(cleaned, 0)
        diff = count_this_week - count_last_week
        
        initiative_count_labels.append(cleaned)
        initiative_count_counts.append(count_this_week)
        initiative_count_diffs.append(diff)
        initiative_count_L3plus.append(count_l3)  # You can add this list if needed
    #endregion
    
    #region 6 Initiative Movement to L3+  
    aggregatedLgate = queryTW.all().values('actual_Lgate__LGate').annotate(
        total_value=Sum('Yearly_Planned_Value'),
    )
    
    for item in aggregatedLgate:
        lgateLabels.append(item['actual_Lgate__LGate'] or '(Blank)')
        lgateValues.append(round((item['total_value'] or 0) / 1_000_000, 1))
        #functions_actual_data.append(round((row['total_actual'] or 0) / 1_000_000, 1))
    #endregion
    
    #endregion =============================================================================================================================
     
#except Exception as e:
#    print(traceback.format_exc())
    return render(request, 'management/delivery/delivery.html', {
        'xfunctions':oFunction, 
        "year_range": year_range, 
        'oYear':oYear,
        'oWeeks':oWeeks, 
        'oWeekTW':oWeekTWLW,
        'record':totalRecordCount, 
        'FunnelSize':json.dumps(float(PlannedTW), default=str), 
        'ForecastYTD':json.dumps(float(ForecastTW), default=str),
        'BankedYTD':json.dumps(float(BankedTW), default=str), 
        'TotalBankedTW':TotalBankedTW, 
        'FunnelGrowth':FunnelGrowthTW,
        'funnelBelowG3':funnelBelowG3,
        'pipeLineRobustness':pipeLineRobustness, 
        'oReports':oReports, 
        'deliveryRecogForm':deliveryRecogForm, 
        'deliveryRecognition':deliveryRecognition, 
        'topInitiatives':topInitiatives,
        'LastUpdated':LastUpdated,
                                                             
        #1. Opex Funnel Chart Data
        'actual':actual, 
        'plan':plan,
                                                            
        #2. Banked YTD Pie Chart Data
        'labels': labels, 
        'data': json.dumps(data, default=str), 
        
        #3 Funnel Value by workstream
        'workstream_labels':json.dumps(functions_labels, default=str),
        'workstream_datasets':json.dumps(functions_datasets, default=str),
        
        #4 Initiative Movement to L3+
        'movement_labels': json.dumps(movement_labels), #movement_label
        'value_to_l3': json.dumps(value_to_l3, default=str),
        'count_to_l3': json.dumps(count_to_l3),
        
        #5 Total & New Initiative Count
        'del_initiative_count_labels':json.dumps(initiative_count_labels),
        'del_initiative_count_counts':json.dumps(initiative_count_counts),
        'del_initiative_count_diffs':json.dumps(initiative_count_diffs),
        'del_initiative_count_L3plus':json.dumps(initiative_count_L3plus),
        
        #6 Initiative Movement to L3+  
        'del_lgateValues':json.dumps(lgateValues, default=str),
        'del_lgateLabels':lgateLabels,
        
        #9. Delivery Movement
        'delivery_movement':bankedThisWeek,
        
        #10. Funnel Movement
        'funnel_movement':funnelChangeThisWeek,
        
        #11. Opex Monthly Banking Plan
        'delivery_labels':delivery_labels,
        'delivery_plan_data':json.dumps(delivery_plan_data, default=str),
        'delivery_forecast_data':json.dumps(delivery_forecast_data, default=str),
        'delivery_actual_data':json.dumps(delivery_actual_data, default=str),
        'monthly_initiatives':monthly_initiatives,
        'monthly_initiatives_json':monthly_initiatives_json,
        
        #12 Initiatives by Delivery
        'eastAssetInitiatives':eastAssetInitiatives,
        'westAssetInitiatives':westAssetInitiatives,
        'novAssetInitiatives':novAssetInitiatives,
        
        'east_total_planned': eastAssetTotals['total_planned'] or 0,
        'east_total_actual': eastAssetTotals['total_actual'] or 0,
        
        'west_total_planned': westAssetTotals['total_planned'] or 0,
        'west_total_actual': westAssetTotals['total_actual'] or 0,
        
        'nov_total_planned': novAssetTotals['total_planned'] or 0,
        'nov_total_actual': novAssetTotals['total_actual'] or 0,
        
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

        #14 Upload Commitment Report
        'formUploadWeeklyCommitments': formUploadWeeklyCommitments,
        'weeklyCommitments':weeklyCommitments,
    })