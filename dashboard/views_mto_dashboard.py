from .models import *
from django.db import models
from django.db.models import Q, F, Prefetch
from dashboard.forms import *

from Fit4.models import *
from reports.models import *

import pandas as pd
import json
import numpy as np
import plotly.graph_objects as go
import plotly
#import datetime
from django.core.mail import mail_admins
from decimal import Decimal
from django.utils.timezone import make_aware
from datetime import datetime, timedelta, date



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
        
def convert_decimal_float(df):
    df = df.copy()
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, Decimal)).any():
            df[col] = df[col].astype(float)
    return df

def add_monthly_totals(df, column_prefix):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return df[[f"{month}_{column_prefix}" for month in months]].sum(axis=1)