from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from .models import *
from django.template.loader import render_to_string

@shared_task
def send_weekly_late_items_email():
    today = timezone.now()
    late_initiatives = Initiative.objects.filter(is_active=True, Planned_Date__lt=today).order_by('-Created_Date').exclude(overall_status__name='Completed').exclude(overall_status__name='Cancelled').exclude(overall_status__name='On hold').exclude(overall_status__name='Defer')
    late_actions = Actions.objects.filter(due_date__lt=today).exclude(status__name='Completed').exclude(status__name='Cancelled')

    users = set()
    for i in late_initiatives:
        users.add(i.owner)
        users.add(i.workstream.lead)
        users.add(i.workstream.sponsor)

    for a in late_actions:
        users.add(a.owner)
        users.add(a.initiative.workstream.lead)
        users.add(a.initiative.workstream.sponsor)

    for user in users:
        user_late_initiatives = late_initiatives.filter(owner=user)
        user_late_actions = late_actions.filter(owner=user)

        context = {
            "user": user,
            "late_initiatives": user_late_initiatives,
            "late_actions": user_late_actions,
        }

        message = render_to_string("emails/weekly_late_report.html", context)

        send_mail(
            subject="Weekly Late Initiatives & Actions Report",
            message='',
            html_message=message,
            from_email='no-reply@raecafrica.com',
            recipient_list=[user.email],
            fail_silently=False,
        )