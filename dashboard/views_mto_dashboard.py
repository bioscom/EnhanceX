from .models import *
from django.db import models
from django.db.models import Q, F, Prefetch
from dashboard.forms import *

from Fit4.models import *
from reports.models import *

from django.db.models import Sum, Count

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

from django.db.models.functions import TruncMonth
from collections import defaultdict
import calendar

import hashlib

from django.db.models.functions import ExtractMonth, ExtractYear
from calendar import month_name


def get_color_from_label(label):
    # Generate a color hex from a hash of the label
    hex_color = hashlib.md5(label.encode()).hexdigest()[:6]
    return f'#{hex_color}'

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
        Planned_Date__lt=today
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
def newThreatsOpportunity(initiatives, yyear, unit, recordType, workstream):
    today = make_aware(datetime.today())
    lte_7_days = today - timedelta(days=7)
    
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO'
    ).annotate(
        month=ExtractMonth('Created_Date'),
        year=ExtractYear('Created_Date')
    ).values(
        'month', 'year', 'Workstream__workstreamname'
    ).annotate(
        total_count=Count('id')
    ).order_by('year', 'month')

    queryset=filtering(queryset, yyear, unit, recordType, workstream)
    
    # Get unique months in calendar order
    month_keys = sorted({(item['month'], item['year']) for item in queryset if item['month'] and item['year']})
    month_labels = [f"{month_name[m]} {y}" for m, y in month_keys]

    # Prepare workstream-wise data mapping
    workstreams = set(item['Workstream__workstreamname'] or '(Blank)' for item in queryset)
    dataset_map = {ws: [0] * len(month_labels) for ws in workstreams}

    # Fill values into dataset_map
    for item in queryset:
        ws = item['Workstream__workstreamname'] or '(Blank)'
        key = (item['month'], item['year'])
        index = month_keys.index(key)
        dataset_map[ws][index] = item['total_count']
        
    # Final structure
    context = {
        'labels_new_threats': month_labels,
        'datasets_new_threats': [
            {
                'label': ws,
                'data': counts,
                'backgroundColor': get_color_from_label(ws)
            }
            for ws, counts in dataset_map.items()
        ]
    }

    return context

#8 KPI3: Resolved Threats & Opportunity
def resolvedThreatsOpportunity(initiatives, yyear, unit, recordType, workstream):
    today = make_aware(datetime.today())
    
    # Filter relevant initiatives
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO',
        overall_status__name__icontains='Completed'
    ).annotate(
        month=ExtractMonth('Created_Date'),
        year=ExtractYear('Created_Date')
    ).values(
        'month', 'year', 'Workstream__workstreamname'
    ).annotate(
        total_count=Count('id')
    ).order_by('year', 'month')

    queryset=filtering(queryset, yyear, unit, recordType, workstream)
    
     # Get unique months in calendar order
    month_keys = sorted({(item['month'], item['year']) for item in queryset if item['month'] and item['year']})
    month_labels = [f"{month_name[m]} {y}" for m, y in month_keys]

    # Prepare workstream-wise data mapping
    workstreams = set(item['Workstream__workstreamname'] or '(Blank)' for item in queryset)
    dataset_map = {ws: [0] * len(month_labels) for ws in workstreams}
    
    # Fill values into dataset_map
    for item in queryset:
        ws = item['Workstream__workstreamname'] or '(Blank)'
        key = (item['month'], item['year'])
        index = month_keys.index(key)
        dataset_map[ws][index] = item['total_count']
        

    # # Truncate date to month and group by month + workstream
    # aggregated = queryset.annotate(month=TruncMonth('Created_Date')).values('month', 'Workstream__workstreamname').annotate( total_count=Count('id')).order_by('month')

    # # Prepare x-axis: unique sorted months
    # month_labels = sorted({item['month'].strftime('%B %Y') for item in aggregated})

    # # Prepare workstream-wise data mapping
    # workstreams = set(item['Workstream__workstreamname'] or '(Blank)' for item in aggregated)
    # dataset_map = {ws: [0] * len(month_labels) for ws in workstreams}

    # Fill in counts
    # for item in aggregated:
    #     ws = item['Workstream__workstreamname'] or '(Blank)'
    #     month_str = item['month'].strftime('%B %Y')
    #     index = month_labels.index(month_str)
    #     dataset_map[ws][index] = item['total_count']
    
     # Fill values into dataset_map
    for item in queryset:
        ws = item['Workstream__workstreamname'] or '(Blank)'
        key = (item['month'], item['year'])
        index = month_keys.index(key)
        dataset_map[ws][index] = item['total_count']

    # Final structure
    context = {
        'labels_resolved_threats': month_labels,
        'datasets_resolved_threats': [
            {
                'label': ws,
                'data': counts,
                'backgroundColor': get_color_from_label(ws)
            }
            for ws, counts in dataset_map.items()
        ]
    }

    return context

#9 KPI4: Overdue Threats & Opportunities
def overDueThreatsOpportunities(initiatives, yyear, unit, recordType, workstream):
    today = datetime.today() #make_aware(datetime.today())
    gte_30_days = today + timedelta(days=30)
    
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO',
        Planned_Date__lt=today
    ).annotate(
        month=ExtractMonth('Created_Date'),
        year=ExtractYear('Created_Date')
    ).values(
        'month', 'year', 'Workstream__workstreamname'
    ).annotate(
        total_count=Count('id')
    ).order_by('year', 'month')
    
    queryset=filtering(queryset, yyear, unit, recordType, workstream)
    
    # Get unique months in calendar order
    month_numbers = sorted({item['month'] for item in queryset if item['month']})
    month_labels = [month_name[m] for m in month_numbers]
    
    # Prepare workstream-wise data mapping
    workstreams = set(item['Workstream__workstreamname'] or '(Blank)' for item in queryset)
    dataset_map = {ws: [0] * len(month_labels) for ws in workstreams}

    # Fill in counts
    for item in queryset:
        ws = item['Workstream__workstreamname'] or '(Blank)'
        month_index = month_numbers.index(item['month'])
        dataset_map[ws][month_index] = item['total_count']

    # Final structure
    context = {
        'labels_overDue_threats': month_labels,
        'datasets_overDue_threats': [
            {
                'label': ws,
                'data': counts,
                'backgroundColor': get_color_from_label(ws)
            }
            for ws, counts in dataset_map.items()
        ]
    }

    return context

#10 MTO KPI5 - Total Threats/Opportunity Score
def totalThreatsOpportunities(initiatives, yyear, unit, recordType, workstream):
    # Assume model: Initiative with fields: status, created_date

    #yyear = request.GET.get('year', datetime.now().year)

    #queryset = initiatives.objects.filter(created_date__year=yyear)
    
    # Group by month + status
    queryset = initiatives.annotate(
        month=ExtractMonth('Created_Date'),
        year=ExtractYear('Created_Date')
    ).values(
        'month', 'year', 'overall_status'
    ).annotate(
        total_mtoscore=Sum('mto_score')
    ).order_by('year', 'month')

    queryset=filtering(queryset, yyear, unit, recordType, workstream)
    
    # Define status groups
    ACTIVE_STATUSES = {
        'New Entry - Active',
        'Needs attention - Active',
        'On track - Active',
        'Completed - Active',
        'TA_Proj-On Track - Active'
    }

    INACTIVE_STATUSES = {
        'On hold - Inactive',
        'Defer - Inactive',
        'Cancelled - Inactive'
    }
    
    # Default dict to accumulate scores per month
    monthly_map = defaultdict(lambda: {'Active': 0, 'Inactive': 0})

    for item in queryset:
        month_num = item['month']
        status = item['overall_status']
        score = item['total_mtoscore'] or 0

        if status in ACTIVE_STATUSES:
            monthly_map[month_num]['Active'] += score
        elif status in INACTIVE_STATUSES:
            monthly_map[month_num]['Inactive'] += score
        # Skip anything unrecognized

    # Prepare containers
    month_labels = []
    active_data = []
    inactive_data = []
    sum_data = []

    for m in sorted(monthly_map.keys()):
        month_labels.append(f"{month_name[m]} {yyear}")
        a = monthly_map[m]['Active']
        i = monthly_map[m]['Inactive']
        active_data.append(a)
        inactive_data.append(i)
        sum_data.append(a + i)

    context = {
        'month_labels': month_labels,
        'active_data': active_data,
        'inactive_data': inactive_data,
        'sum_data': sum_data,
    }

    return context

#11 All ACTIVE Threats and Opportunities Report 
def activeThreatsOpport(initiatives, yyear, unit, recordType, workstream, initovrsC, initovrsH, initovrsD, initovrsCa):
    queryset = initiatives.filter(
        Workstream__workstreamname__icontains='MTO', 
    ).exclude(Q(overall_status=initovrsC)).exclude(Q(overall_status=initovrsH)).exclude(Q(overall_status=initovrsD)).exclude(Q(overall_status=initovrsCa))
    
    page_obj = filtering(queryset, yyear, unit, recordType, workstream)
    return page_obj

def filtering(queryset, yyear, unit, recordType, workstream):
    if yyear is None or yyear == 'All':
        queryset = queryset.all()
        
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
    if yyear is None or yyear == 'All':
        queryset = queryset.all()
        
    if yyear and yyear != 'All':
        queryset = queryset.filter(Created_Date__year=yyear)
    
    if unit and unit != 'All':
        queryset = queryset.filter(initiative__unit__pk=unit)

    if recordType and recordType != 'All':
        queryset = queryset.filter(initiative__recordType__pk=recordType)

    if workstream and workstream != 'All':
        queryset = queryset.filter(initiative__Workstream__pk=workstream)
        
    return queryset