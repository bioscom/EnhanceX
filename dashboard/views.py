from .models import *
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.db.models import Q, F, Prefetch
from dashboard.forms import *
import traceback
from django.utils.crypto import get_random_string
from Fit4.models import *
from reports.models import *
from urllib.parse import urlparse
from urllib.parse import parse_qs
from math import pi
import plotly.express as px
import pandas as pd
from django.shortcuts import render
from plotly.io import to_html
import json
import numpy as np
import plotly.graph_objects as go
import plotly
from django.db.models import Sum
#import datetime

import dash 
from dash import Dash, dcc, html, Input, Output, dash_table
from django.core.mail import mail_admins
from decimal import Decimal
from django.utils.timezone import make_aware
from datetime import datetime, timedelta, date

from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db import connections
from django.contrib import messages
import pytz
from django.db.models import Sum, Count
from django.utils import timezone
from django.db.models.functions import ExtractWeek, ExtractYear


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


#region ============================ Plotly Graphs =======================================

def add_monthly_totals(df, column_prefix):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return df[[f"{month}_{column_prefix}" for month in months]].sum(axis=1)

def convert_decimal_float(df):
    df = df.copy()
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, Decimal)).any():
            df[col] = df[col].astype(float)
    return df

def chart_wrapper(func):
    def wrapper(df):
        try:
            chart = func(df)
            return to_html(chart, full_html=False)
        except Exception:
            print(traceback.format_exc())
            return ""
    return wrapper


#@chart_wrapper
def doughnutPlanChart(df):
    doughnut_chart_html = ""
    try:
        df = convert_decimal_float(df)
        numeric_cols = df.select_dtypes(include='number').columns
        df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()
        print(df)
        df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']

        # Select the data points to be plotted
        wrk = df['WorkstreamName']
        Plan = df['Plan']

        data = {'Workstream': wrk, 'Plan': Plan}
        df=pd.DataFrame(data)
        doughnut_chart = px.pie(df, names="Workstream", values="Plan", title=" Plan By Workstream", hole=0.5)
        doughnut_chart.update_traces(text=df["Plan"].apply(lambda x: f"{round(x/1000000, 1):,}M"), textinfo="text")
        s=df["Plan"].sum()/1000000
        doughnut_chart.add_annotation(text=f"{round(s, 1):,}M", x=0.5, y=0.5, showarrow=False, font=dict(size=20, family="Arial", color="black"))
        doughnut_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

        # Convert to HTML
        doughnut_chart_html = to_html(doughnut_chart, full_html=False)
    except Exception as e:
        print(traceback.format_exc())
    return doughnut_chart_html

#@chart_wrapper
def doughnutActualChart(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()

    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']

    # Select the data points to be plotted
    wrk = df['WorkstreamName']
    Actual = df['Actual']

    data = {'Workstream': wrk, 'Actual': Actual}
    df=pd.DataFrame(data)
    doughnut_chart = px.pie(df, names="Workstream", values="Actual", title="Actual By Workstream", hole=0.5)
    doughnut_chart.update_traces(text=df["Actual"].apply(lambda x: f"{round(x/1000000, 1):,}M"), textinfo="text")
    s=df["Actual"].sum()/1000000
    doughnut_chart.add_annotation(text=f"{round(s, 1):,}M", x=0.5, y=0.5, showarrow=False, font=dict(size=20, family="Arial", color="black"))
    doughnut_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    doughnut_chart_html = to_html(doughnut_chart, full_html=False)

    return doughnut_chart_html

#@chart_wrapper
def VerticalBarChart(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()

    df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']
    df['Forecast'] = add_monthly_totals(df, 'Forecast') #df['Jan_Forecast'] + df['Feb_Forecast'] + df['Mar_Forecast'] + df['Apr_Forecast'] + df['May_Forecast'] + df['Jun_Forecast'] + df['Jul_Forecast'] + df['Aug_Forecast'] + df['Sep_Forecast'] + df['Oct_Forecast'] + df['Nov_Forecast'] + df['Dec_Forecast']

    # Select the data points to be plotted
    wrk = df['WorkstreamName']
    Plan = df['Plan']
    Forecast = df['Forecast']
    Actual = df['Actual']

    data = {'Workstream': wrk, 'Plan': Plan, "Forecast":Forecast, "Actual":Actual}

    df=pd.DataFrame(data)
    #print(df)

    # Convert from wide to long format for plotly (grouped bar format)
    df_melted = df.melt(id_vars=["Workstream"], var_name="Category", value_name="Value")

    # Convert numbers to millions and round to 1 decimal place
    df_melted["Formatted Value"]= df_melted["Value"].apply(lambda x: f"{round(x/1000000, 1):,}M")

    grouped_bar_chart = px.bar(df_melted, x="Workstream", y="Value", color="Category", title="Plan Forecast & Actual By Workstream", barmode="group", text="Formatted Value")
    grouped_bar_chart.update_traces(texttemplate="%{text}", textposition="auto")
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html

#@chart_wrapper
def HorizontalBarChart(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()

    df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']
    df['Forecast'] = add_monthly_totals(df, 'Forecast') #df['Jan_Forecast'] + df['Feb_Forecast'] + df['Mar_Forecast'] + df['Apr_Forecast'] + df['May_Forecast'] + df['Jun_Forecast'] + df['Jul_Forecast'] + df['Aug_Forecast'] + df['Sep_Forecast'] + df['Oct_Forecast'] + df['Nov_Forecast'] + df['Dec_Forecast']

    # Select the data points to be plotted
    wrk = df['WorkstreamName']
    Plan = df['Plan']
    Forecast = df['Forecast']
    Actual = df['Actual']

    data = {'Workstream': wrk, 'Plan': Plan, "Forecast":Forecast, "Actual":Actual}

    df=pd.DataFrame(data)
    #print(df)

    # Convert from wide to long format for plotly (grouped bar format)
    df_melted = df.melt(id_vars=["Workstream"], var_name="Category", value_name="Value")

    # Convert numbers to millions and round to 1 decimal place
    df_melted["Formatted Value"]= df_melted["Value"].apply(lambda x: f"{round(x/1000000, 1):,}M")

    grouped_bar_chart = px.bar(df_melted, x="Value", y="Workstream", color="Category", title="Plan Chart", orientation='h', barmode="group", text="Formatted Value")
    grouped_bar_chart.update_traces(texttemplate="%{text}", textposition="auto")
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html

#@chart_wrapper
def VerticalBarChartByFunctions(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('functions', as_index =False)[numeric_cols].sum()

    df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']
    df['Forecast'] = add_monthly_totals(df, 'Forecast') #df['Jan_Forecast'] + df['Feb_Forecast'] + df['Mar_Forecast'] + df['Apr_Forecast'] + df['May_Forecast'] + df['Jun_Forecast'] + df['Jul_Forecast'] + df['Aug_Forecast'] + df['Sep_Forecast'] + df['Oct_Forecast'] + df['Nov_Forecast'] + df['Dec_Forecast']

    # Select the data points to be plotted
    function = df['functions']
    Plan = df['Plan']
    Forecast = df['Forecast']
    Actual = df['Actual']

    data = {'Function': function, 'Plan': Plan, "Forecast":Forecast, "Actual":Actual}

    df=pd.DataFrame(data)
    #print(df)

    # Convert from wide to long format for plotly (grouped bar format)
    df_melted = df.melt(id_vars=["Function"], var_name="Category", value_name="Value")

    # Convert numbers to millions and round to 1 decimal place
    df_melted["Formatted Value"]= df_melted["Value"].apply(lambda x: f"{round(x/1000000, 1):,}M")

    grouped_bar_chart = px.bar(df_melted, x="Function", y="Value", color="Category", title="Plan, Forecast and Actual By Funcions", barmode="group", text="Formatted Value")
    grouped_bar_chart.update_traces(texttemplate="%{text}", textposition="auto")
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html

#@chart_wrapper
def VerticalBarChartByLGates(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('ActualLGate', as_index =False)[numeric_cols].sum()

    df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    df['Actual'] = add_monthly_totals(df, 'Actual') #df['Jan_Actual'] + df['Feb_Actual'] + df['Mar_Actual'] + df['Apr_Actual'] + df['May_Actual'] + df['Jun_Actual'] + df['Jul_Actual'] + df['Aug_Actual'] + df['Sep_Actual'] + df['Oct_Actual'] + df['Nov_Actual'] + df['Dec_Actual']
    df['Forecast'] = add_monthly_totals(df, 'Forecast') #df['Jan_Forecast'] + df['Feb_Forecast'] + df['Mar_Forecast'] + df['Apr_Forecast'] + df['May_Forecast'] + df['Jun_Forecast'] + df['Jul_Forecast'] + df['Aug_Forecast'] + df['Sep_Forecast'] + df['Oct_Forecast'] + df['Nov_Forecast'] + df['Dec_Forecast']

    # Select the data points to be plotted
    ActualL_Gate = df['ActualLGate']
    Plan = df['Plan']
    Forecast = df['Forecast']
    Actual = df['Actual']

    data = {'ActualL_Gate': ActualL_Gate, 'Plan': Plan, "Forecast":Forecast, "Actual":Actual}

    df=pd.DataFrame(data)
    #print(df)

    # Convert from wide to long format for plotly (grouped bar format)
    df_melted = df.melt(id_vars=["ActualL_Gate"], var_name="Category", value_name="Value")

    # Convert numbers to millions and round to 1 decimal place
    df_melted["Formatted Value"] = df_melted["Value"].apply(lambda x: f"{round(x/1000000, 1):,}M")

    grouped_bar_chart = px.bar(df_melted, x="ActualL_Gate", y="Value", color="Category", title="Plan By LGate", barmode="group", text="Formatted Value")
    grouped_bar_chart.update_traces(texttemplate="%{text}", textposition="auto")
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html

#@chart_wrapper
def ChartCountByLGates(df):
    df = convert_decimal_float(df)
    numeric_cols = df.select_dtypes(include='number').columns
    df = df.groupby('ActualLGate', as_index =False)[numeric_cols].sum()

    #print(df)
    # Select the data points to be plotted
    ActualL_Gate = df['ActualLGate']
    Count = df['initiative_id']

    data = {'ActualL_Gate': ActualL_Gate, 'Count': Count}

    df=pd.DataFrame(data)
    
    grouped_bar_chart = px.bar(df, x="ActualL_Gate", y="Count", title="Count By LGate", barmode="group")
    grouped_bar_chart.update_traces(textposition="auto", text=Count)
    grouped_bar_chart.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), autosize=True)

    # Convert to HTML
    bar_chart_html = to_html(grouped_bar_chart, full_html=False)

    return bar_chart_html


def VerticalBarChartByInLast7Days(request):
    # Get today's date
    today = timezone.now()

    # Get data from the last 7 days
    last_7_days = today - timezone.timedelta(days=7)

    queryset=InitiativeImpact.objects.select_related('initiative').annotate(
            Workstream=F('initiative__Workstream'),
            WorkstreamName=F('initiative__Workstream__workstreamname'),
            HashTag=F('initiative__HashTag'),
            functions=F('initiative__functions__title'),
            Year=F('initiative__YYear'),
            overall_status=F('initiative__overall_status'),
            Plan_Relevance=F('initiative__Plan_Relevance'), 
            ActualLGate=F('initiative__actual_Lgate__LGate'),
            enabledby=F('initiative__enabledby')).filter(initiative__Created_Date__gte=last_7_days).values()
    
    if queryset.exists():
        # Convert to Pandas DataFrame
        df=pd.DataFrame(list(queryset))
        df=df.drop(columns=['last_modified_date', 'Created_Date'])
        df.replace(to_replace=[None], value=0, inplace=True)

        df = convert_decimal_float(df)
        numeric_cols = df.select_dtypes(include='number').columns
        df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()
        df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    
        if not df.empty:
            # Create the Plotly figure
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["WorkstreamName"],
                y=df["Plan"],
                text=df["Plan"].apply(lambda x: f"{round(x/1000000, 1):,}M"),
                textposition="auto",
                marker=dict(color="blue")
            ))

            # Format the layout
            fig.update_layout(
                title="Initiatives Created in the Last 7 Days",
                xaxis_title="Workstream",
                yaxis_title="Sum of Plan",
                # height=460, 
                # width=500,
                margin=dict(l=40, r=40, t=40, b=40),
                plot_bgcolor="rgba(0,0,0,0)",
            )
            # Convert Plotly figure to JSON
            graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        else:
            graph_json = None
        return graph_json
    else:
        graph_json = None
    return graph_json

#endregion================================================================================

#region ============================== MTO Dashboard ============================

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
def get_years():
    date_range = 7 
    current_year = datetime.now().year
    return list(range(current_year - date_range, current_year + 1))

def get_weeks(year):
    # First Monday of the year (or the first week starting on Monday)
    d = datetime.date(year, 1, 1)
    d += datetime.timedelta(days=(7 - d.weekday()) % 7)  # move to next Monday if not already Monday

    weeks = []
    try:
        while d.year == year:
            week_start = d
            week_end = d + datetime.timedelta(days=6)
            weeks.append((week_start, week_end))
            d += datetime.timedelta(weeks=1)
    except Exception as e:
        print(traceback.format_exc())
    return weeks

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
    
    
        overDueActions = actionsOverDue(yyear, unit, recordType, workstream, ovrsC, ovrsH, ovrsCa)                                       #1 of MTO Actions Overdue with summary
        actionsDueIn30Days = actionsOverDueIn30Days(yyear, unit, recordType, workstream, ovrsC, ovrsH, ovrsCa)                           #2 Open MTO Actions Due within 30 days
        
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


#1 # of MTO Actions Overdue with summary
def actionsOverDue(yyear, unit, recordType, workstream, ovrsC, ovrsH, ovrsCa):
    queryset = Actions.objects.filter(
        initiative__Workstream__workstreamname__icontains='MTO',
        due_date__lt=make_aware(datetime.today())
    ).select_related('initiative').exclude(Q(status=ovrsC)).exclude(Q(status=ovrsH)).exclude(Q(status=ovrsCa))
    
    overDueActions =  actionfiltering(queryset, yyear, unit, recordType, workstream)
    return overDueActions

#2 Open MTO Actions Due within 30 days
def actionsOverDueIn30Days(yyear, unit, recordType, workstream, ovrsC, ovrsH, ovrsCa):
    today = make_aware(datetime.today())
    in_30_days = today + timedelta(days=30)
    
    queryset = Actions.objects.filter(
        initiative__Workstream__workstreamname__icontains='MTO',
        due_date__gte=today,
        due_date__lte=in_30_days
    ).select_related('initiative').exclude(Q(status=ovrsC)).exclude(Q(status=ovrsH)).exclude(Q(status=ovrsCa))
       
    actionsDueIn30Days =  actionfiltering(queryset, yyear, unit, recordType, workstream)
    return actionsDueIn30Days

#3 Threats and Opportunities Due in 30 days
def threatsDueIn30Days(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa):
    today = make_aware(datetime.today())
    in_30_days = today + timedelta(days=30)
    
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO', 
        Planned_Date__gte=today,
        Planned_Date__lte=in_30_days
    ).exclude(Q(overall_status=initovrsC)).exclude(Q(overall_status=initovrsH)).exclude(Q(overall_status=initovrsD)).exclude(Q(overall_status=initovrsCa))
    
    threatsIn30Days = filtering(queryset, yyear, unit, recordType, workstream)
    return threatsIn30Days

#4 Overdue Threats and Opportunities
def OverDueThreatsOpportunity(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa):
    today = make_aware(datetime.today())
    in_30_days = today + timedelta(days=30)
    
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO',
        Planned_Date__gte=in_30_days
    ).exclude(Q(overall_status=initovrsC)).exclude(Q(overall_status=initovrsH)).exclude(Q(overall_status=initovrsD)).exclude(Q(overall_status=initovrsCa))
    
    overDueThreatsOpportunity = filtering(queryset, yyear, unit, recordType, workstream)
    return overDueThreatsOpportunity
 
#5 Top 20 Threats & Opportunities (L3 - L5)
def top20ThreatsOpport(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa):
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO',
        actual_Lgate__GateIndex__gte=3
    ).exclude(Q(overall_status=initovrsC)).exclude(Q(overall_status=initovrsH)).exclude(Q(overall_status=initovrsD)).exclude(Q(overall_status=initovrsCa)).order_by('-mto_score')
    
    obj_top20Threats =  filtering(queryset, yyear, unit, recordType, workstream)[:20]
    return obj_top20Threats

#6 Threats & Opportunities at L0 to L2
def threatsOpportL2(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa):
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO',
        actual_Lgate__GateIndex__lte=2
    ).exclude(Q(overall_status=initovrsC)).exclude(Q(overall_status=initovrsH)).exclude(Q(overall_status=initovrsD)).exclude(Q(overall_status=initovrsCa)).order_by('-mto_score')
     
    threatOpportunityatL2 = filtering(queryset, yyear, unit, recordType, workstream)
    return threatOpportunityatL2

#7 KPI1: New Threats & Opportunity
#8 KPI3: Resolved Threats & Opportunity
#9 KPI4: Overdue Threats & Opportunity
#10 MTO KPI5 - Total Threats/Opportunity Score

#11 All ACTIVE Threats and Opportunities Report 
def activeThreatsOpport(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa):
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO', 
    ).exclude(Q(overall_status=initovrsC)).exclude(Q(overall_status=initovrsH)).exclude(Q(overall_status=initovrsD)).exclude(Q(overall_status=initovrsCa))
    
    page_obj = filtering(queryset, yyear, unit, recordType, workstream)
    return page_obj


def filtering(queryset, yyear, unit, recordType, workstream):
    if yyear is None:
        oYear = datetime.today().year
        queryset = queryset.filter(Created_Date__year=oYear)
        
    if yyear and yyear != 'All':
        queryset = queryset.filter(Created_Date__year=yyear)
    
    if unit and unit != 'All':
        queryset = queryset.filter(unit__pk=unit)

    if recordType and recordType != 'All':
        queryset = queryset.filter(recordType__pk=recordType)

    if workstream and workstream != 'All':
        queryset = queryset.filter(Workstream__pk=workstream)
        
    return queryset

def actionfiltering(queryset, yyear, unit, recordType, workstream):
    if yyear is None:
        oYear = datetime.today().year
        queryset = queryset.filter(Created_Date__year=oYear)
        
    if yyear and yyear != 'All':
        queryset = queryset.filter(Created_Date__year=yyear)
    
    if unit and unit != 'All':
        queryset = queryset.filter(initiative__unit__pk=unit)

    if recordType and recordType != 'All':
        queryset = queryset.filter(initiative__recordType__pk=recordType)

    if workstream and workstream != 'All':
        queryset = queryset.filter(initiative__Workstream__pk=workstream)
        
    return queryset

def KPI1NewThreatsOpportunity(request):
    pass

def KPI3ResolvedThreatsOpportunity(request):
    pass

def KPI4OverdueThreatsOpportunity(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa):
    today = make_aware(datetime.today())
    in_30_days = today + timedelta(days=30)
    
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO',
        Planned_Date__gte=in_30_days
    ).exclude(Q(overall_status=initovrsC)).exclude(Q(overall_status=initovrsH)).exclude(Q(overall_status=initovrsD)).exclude(Q(overall_status=initovrsCa))
    
    queryset = filtering(queryset, yyear, unit, recordType, workstream)
    
    if queryset.exists():
        # Convert to Pandas DataFrame
        df=pd.DataFrame(list(queryset))
        df=df.drop(columns=['last_modified_date', 'Created_Date'])
        df.replace(to_replace=[None], value=0, inplace=True)

        df = convert_decimal_float(df)
        numeric_cols = df.select_dtypes(include='number').columns
        df = df.groupby('WorkstreamName', as_index =False)[numeric_cols].sum()
        df['Plan'] = add_monthly_totals(df, 'Plan') #df['Jan_Plan'] + df['Feb_Plan'] + df['Mar_Plan'] + df['Apr_Plan'] + df['May_Plan'] + df['Jun_Plan'] + df['Jul_Plan'] + df['Aug_Plan'] + df['Sep_Plan'] + df['Oct_Plan'] + df['Nov_Plan'] + df['Dec_Plan']
    
        if not df.empty:
            # Create the Plotly figure
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["WorkstreamName"],
                y=df["Plan"],
                text=df["Plan"].apply(lambda x: f"{round(x/1000000, 1):,}M"),
                textposition="auto",
                marker=dict(color="blue")
            ))

            # Format the layout
            fig.update_layout(
                title="Initiatives Created in the Last 7 Days",
                xaxis_title="Workstream",
                yaxis_title="Sum of Plan",
                # height=460, 
                # width=500,
                margin=dict(l=40, r=40, t=40, b=40),
                plot_bgcolor="rgba(0,0,0,0)",
            )
            # Convert Plotly figure to JSON
            graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        else:
            graph_json = None
        return graph_json
    else:
        graph_json = None
    return graph_json
    

def KPI5MTOTotalThreatsOpportunity(request):
    pass
        
#endregion ====================================================================

#region ================================ Management Reporting =========================================================

def list_reports(request):
    oReports = SavedFilter.objects.all()
    
    return None

def handle_weekly_report(request, model, show_current_func, show_last_func, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range):
    if model.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW).first():
        return show_current_func(request, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range)
    else:
        messages.warning(request, f"No record for the current week {oWeekTW}, click on sync this week data.")
        return show_last_func(request, oWeekLW, oYear, oWeeks, oFunction, year_range)
    

def management_report(request, report_year=None, report_week=None):
    try:
        if request.method == "POST":
            selected_year = request.POST.get('selected_year')
            print(f"Selected via AJAX: {selected_year}")
        else:
            selected_year = datetime.now().year  # Default on GET
        
        year_range = list_years_from2018() #range(2018, 2031)
        
        today = datetime.now().today()
        oYear = today.year if not report_year or report_year == 'None' else report_year
        
        oWeeks = get_weeks_in_year(oYear)
        oFunction = Functions.objects.all() 
        
        oWeekTW = today.isocalendar().week if not report_week or report_week == 'None' else report_week
        oWeekLW = oWeekTW - 1
        
        
        selected_tab = request.GET.get('tab', 'Opex')  # default to Opex
        if selected_tab == "Opex":
            return handle_weekly_report(request, opex_weekly_Initiative_Report, showThisWeek, showLastWeek, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range)
        elif selected_tab == "Delivery":
            return handle_weekly_report(request, delivery_weekly_Initiative_Report, showDeliveryThisWeek, showDeliveryLastWeek, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range)
        
        # if opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW).first():
        #     return showThisWeek(request, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range)
        # else:
        #     messages.warning(request, "No record for the current week " + str(oWeekTW) + " , click on sync this week data.")
        #     return showLastWeek(request, oWeekLW, oYear, oWeeks, oFunction, year_range)
        
        # if delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW).first():
        #     return showDeliveryThisWeek(request, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range)
        # else:
        #     messages.warning(request, "No record for the current week " + str(oWeekTW) + " , click on sync this week data.")
        #     return showDeliveryLastWeek(request, oWeekLW, oYear, oWeeks, oFunction, year_range)
            
    except Exception as e:
        print(traceback.format_exc())   
    return redirect(reverse("Fit4:home"))
  

#region ============================================== Opex Data Management ==================================================================       

def showThisWeek(request, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range):
    try:
        opexRecognition = opex_weekly_recognition.objects.filter(report_week=oWeekTW, Created_Date__year=oYear).first()
        opexRecogForm = opexRecognitionForm(instance=opexRecognition)
        
        queryTW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW)
        queryLW = opex_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
    except Exception as e:
         print(traceback.format_exc())
    return OpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, opexRecogForm, opexRecognition, oWeekTW, oWeeks)

def showLastWeek(request, oWeekLW, oYear, oWeeks, oFunction, year_range):
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
            funnelBelowG3=round(PlannedTW/funnelBelowG3, 1)
        else: 
            funnelBelowG3=0
            
        #5. Funnel Growth
        FunnelGrowthTW=PlannedTW - PlannedLW
        
        #6. Total Banked Value
        TotalBankedTW=BankedTW - BankedLW
        
        #6. Total Record Count
        #totalRecordCount=queryTW.filter(condition=True).count()
        if queryTW.exists():
            totalRecordCount = queryTW.count()
        else:
            totalRecordCount = 0
        
        #7. Top Initiatives by Value
        topInitiatives=queryTW.order_by('-Yearly_Planned_Value')
        
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
    return render(request, 'management/managementReport.html', {'xfunctions':oFunction, "year_range": year_range, 'oWeeks':oWeeks, 'oWeekTW':oWeekTWLW,
                                                                'record':totalRecordCount, 'FunnelSize':PlannedTW, 'ForecastYTD':ForecastTW,
                                                                'BankedYTD':BankedTW, 'TotalBankedTW':TotalBankedTW, 'FunnelGrowth':FunnelGrowthTW,
                                                                'funnelBelowG3':funnelBelowG3,
                                                                'pipeLineRobustness':pipeLineRobustness, 'oReports':oReports, 'opexRecogForm':opexRecogForm, 
                                                                'opexRecognition':opexRecognition, 'topInitiatives':topInitiatives, 'LastUpdated':LastUpdated,
                                                                
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
                                                            })

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

    # Filter records by year
    queryset = InitiativeImpact.objects.filter(YYear=selected_year)
    
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

def add_opex_recognition(request, id=None):
    try:
        if id:
            edit_opex_recognition(request, id)
            return redirect(reverse("dashboard:management_report"))
        
        if request.method == "POST":
            form = opexRecognitionForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.created_by = request.user
                o.last_modified_by = request.user
                o.report_week = get_report_week()
                o.save()
                messages.success(request, '<b>Recognition added successfully.</b>')
                return redirect(reverse("dashboard:management_report"))
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
                messages.success(request, '<b>Recognition added successfully.</b>')
                return redirect(reverse("dashboard:management_report"))
        else:
            form = opexRecognitionForm(instance=recogntion)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_opex_recognition.html", {'opex': form})

# This copies data for the week to the Model
def trigger_opex_data_copy(request):
    if request.method == "POST":
        selected_id = request.POST.get('selected_id')  # Always returns a row
        # Get current time in your timezone (e.g., Africa/Lagos)
        #now = datetime.now(pytz.timezone("Africa/Lagos"))
        now = timezone.now()
        current_week = now.isocalendar()[1]  # ISO week number (1–53)
        current_year = now.year
        
        if now.weekday() != 4 or now.hour < 9:
            messages.error(request, "⚠️ Sync only allowed after 9am on Fridays.")
            return redirect('/en/management_report')
        
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
                    Date_Downloaded = now.date(),
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
        return redirect('/en/management_report')

#endregion =======================================================================================================================================

#region ============================================== Delivery Data Management ==================================================================  
# This copies data for the week to the Model
def trigger_delivery_data_copy(request, model):
    if request.method == "POST":
        selected_id = request.POST.get('selected_id')  # Always returns a row
        # Get current time in your timezone (e.g., Africa/Lagos)
        #now = datetime.now(pytz.timezone("Africa/Lagos"))
        now = timezone.now()
        current_week = now.isocalendar()[1]  # ISO week number (1–53)
        current_year = now.year
        
        if now.weekday() != 4 or now.hour < 9:
            messages.error(request, "⚠️ Sync only allowed after 9am on Fridays.")
            return redirect('/en/management_report')
        
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
                    Date_Downloaded = now.date(),
                    created_by = o.initiative.created_by,
                    report_week = current_week,
                )
                for o in query
            ]
            
            # Before bulk create, check if data has already been downloaded for the week

            has_this_week_data = delivery_weekly_Initiative_Report.objects.annotate(week=ExtractWeek('Date_Downloaded'), year=ExtractYear('Date_Downloaded')).filter(Date_Downloaded__year=current_year, Date_Downloaded__week=current_week,)
            if has_this_week_data.exists():
                has_this_week_data.delete()
            
            # Bulk insert into the snapshot model
            delivery_weekly_Initiative_Report.objects.bulk_create(snapshots)
            
            messages.success(request, "✅ Data sync completed successfully.")
        except Exception as e:
            messages.error(request, f"❌ Error during data sync: {str(e)}")
            print(traceback.format_exc(), str(e))
        return redirect('/en/management_report')

def showDeliveryThisWeek(request, oWeekTW, oWeekLW, oYear, oWeeks, oFunction, year_range):
    try:
        deliveryRecognition = delivery_weekly_recognition.objects.filter(report_week=oWeekTW, Created_Date__year=oYear).first()
        deliveryRecogForm = deliveryRecognitionForm(instance=deliveryRecognition)
        
        queryTW = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekTW)
        queryLW = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
    except Exception as e:
         print(traceback.format_exc())
    return OpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, deliveryRecogForm, deliveryRecognition, oWeekTW, oWeeks)

def showDeliveryLastWeek(request, oWeekLW, oYear, oWeeks, oFunction, year_range):
    try:
        oUpperWeek = oWeekLW-1 # Last week / Upper Week Comparism
        deliveryRecognition = delivery_weekly_recognition.objects.filter(report_week=oWeekLW, Created_Date__year=oYear).first()
        deliveryRecogForm = deliveryRecognitionForm(instance=deliveryRecognition)
        
        queryTW = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oWeekLW)
        queryLW = delivery_weekly_Initiative_Report.objects.filter(Date_Downloaded__year=oYear, Date_Downloaded__week=oUpperWeek)
    except Exception as e:
         print(traceback.format_exc())
    return OpexPageLoader(request, queryTW, queryLW, oYear, oFunction, year_range, deliveryRecogForm, deliveryRecognition, oWeekLW, oWeeks)

def add_delivery_recognition(request, id=None):
    try:
        if id:
            edit_delivery_recognition(request, id)
            return redirect(reverse("dashboard:management_report"))
        
        if request.method == "POST":
            form = deliveryRecognitionForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.created_by = request.user
                o.last_modified_by = request.user
                o.report_week = get_report_week()
                o.save()
                messages.success(request, '<b>Recognition added successfully.</b>')
                return redirect(reverse("dashboard:management_report"))
        else:
            form = deliveryRecognitionForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_opex_recognition.html", {'opex': form})

def edit_delivery_recognition(request, id):
    try:
        recogntion = get_object_or_404(delivery_weekly_recognition, id=id)
        if request.method == "POST":
            form = deliveryRecognitionForm(data=request.POST, instance=recogntion)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()
                messages.success(request, '<b>Recognition added successfully.</b>')
                return redirect(reverse("dashboard:management_report"))
        else:
            form = deliveryRecognitionForm(instance=recogntion)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_opex_recognition.html", {'opex': form})




#endregion ======================================================================================================================================= 

#endregion =============================================================================================================================



# Use these lines to start any function in your application
# try:
#   
#    
# except Exception as e:
#         print(traceback.format_exc())

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