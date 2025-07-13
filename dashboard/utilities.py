from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import F, FloatField, ExpressionWrapper
from django.utils.timezone import now
from dashboard.models import *

def get_report_week():
    today = datetime.now().today()
    week_number = today.isocalendar().week
    return week_number

def list_years_from2018():
    date_range = 7
    current_year = datetime.now().year
    return list(range(2018, current_year + 15))

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


def get_weekly_initiative_reports():
    current_year = now().year
    current_week = now().isocalendar().week

    opex_query = opex_weekly_Initiative_Report.objects.filter(
        Date_Downloaded__year=current_year,
        Date_Downloaded__week=current_week
    ).first()
    if opex_query is None:
        opex_query = opex_weekly_Initiative_Report.objects.filter(
            Date_Downloaded__year=current_year,
            Date_Downloaded__week=current_week - 1
        ).first()

    opex_fullybankedInitiatives = opex_weekly_Initiative_Report.objects.filter(
        Date_Downloaded=opex_query.Date_Downloaded,
        Yearly_Actual_value__gte=F('Yearly_Planned_Value'),
        Yearly_Actual_value__gt=0,
        Yearly_Planned_Value__gt=0,
    ).annotate(
        achievement_pct=ExpressionWrapper(
            F('Yearly_Actual_value') * 100.0 / F('Yearly_Planned_Value'),
            output_field=FloatField()
        )
    ).order_by('-achievement_pct')

    opex_notFullybankedInitiatives = opex_weekly_Initiative_Report.objects.filter(
        Date_Downloaded=opex_query.Date_Downloaded,
        Yearly_Actual_value__lt=F('Yearly_Planned_Value')
    ).annotate(
        achievement_pct=ExpressionWrapper(
            F('Yearly_Actual_value') * 100.0 / F('Yearly_Planned_Value'),
            output_field=FloatField()
        )
    ).order_by('-achievement_pct')

    delivery_query = delivery_weekly_Initiative_Report.objects.filter(
        Date_Downloaded__year=current_year,
        Date_Downloaded__week=current_week
    ).first()
    if delivery_query is None:
        delivery_query = delivery_weekly_Initiative_Report.objects.filter(
            Date_Downloaded__year=current_year,
            Date_Downloaded__week=current_week - 1
        ).first()

    delivery_fullybankedInitiatives = delivery_weekly_Initiative_Report.objects.filter(
        Date_Downloaded=delivery_query.Date_Downloaded,
        Yearly_Actual_value__gte=F('Yearly_Planned_Value'),
        Yearly_Actual_value__gt=0,
        Yearly_Planned_Value__gt=0,
    ).annotate(
        achievement_pct=ExpressionWrapper(
            F('Yearly_Actual_value') * 100.0 / F('Yearly_Planned_Value'),
            output_field=FloatField()
        )
    ).order_by('-achievement_pct')

    delivery_notFullybankedInitiatives = delivery_weekly_Initiative_Report.objects.filter(
        Date_Downloaded=delivery_query.Date_Downloaded,
        Yearly_Actual_value__lt=F('Yearly_Planned_Value')
    ).annotate(
        achievement_pct=ExpressionWrapper(
            F('Yearly_Actual_value') * 100.0 / F('Yearly_Planned_Value'),
            output_field=FloatField()
        )
    ).order_by('-achievement_pct')

    return {
        'opex_fullybankedInitiatives': opex_fullybankedInitiatives,
        'opex_notFullybankedInitiatives': opex_notFullybankedInitiatives,
        'delivery_fullybankedInitiatives': delivery_fullybankedInitiatives,
        'delivery_notFullybankedInitiatives': delivery_notFullybankedInitiatives,
    }