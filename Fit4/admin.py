from django.contrib import admin
from .models import *

from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

#admin.site.register(Asset_Hierarchy)
admin.site.register(Workstream)
admin.site.register(Initiative)
admin.site.register(InitiativeImpact)
admin.site.register(BenefitType)

admin.site.register(Functions)
admin.site.register(SavingsType)
admin.site.register(PlanRelevance)
admin.site.register(TeamMembers)
admin.site.register(Actions)
admin.site.register(action_status)
admin.site.register(action_type)

@admin.register(Actual_L_Gate)
class Actual_L_GateAdmin(admin.ModelAdmin):
    list_display=('LGate', 'GateIndex')
    #list_filter=('is_approved', 'author', 'dateTime') 
    
admin.site.register(EnabledBy)
admin.site.register(Discipline)
admin.site.register(Currency)
admin.site.register(Frequency)
admin.site.register(approvalStatusVisual)

admin.site.register(InitiativeNotes)
admin.site.register(InitiativeFiles)
admin.site.register(overall_status)
admin.site.register(record_type)
#admin.site.register(Unit)
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display=('name', 'rated_capacity', 'UOM', 'margin', 'impactDays', 'days')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display=('name', 'url', 'icon', 'parent', 'order')

@admin.register(MTOScoring)
class MTOScoringAdmin(admin.ModelAdmin):
    list_display=('initiative', 'A0', 'B0', 'C0', 'D0', 'E0', 
                  'A1', 'B1', 'C1', 'D1', 'E1',
                  'A2', 'B2', 'C2', 'D2', 'E2',
                  'A3', 'B3', 'C3', 'D3', 'E3',
                  'A4', 'B4', 'C4', 'D4', 'E4',
                  'A5', 'B5', 'C5', 'D5', 'E5',)

admin.site.register(ProactiveType)
admin.site.register(AssetConsequence)
admin.site.register(Threshold)

@admin.register(MTOScoringInfo)
class MTOScoringInfoAdmin(admin.ModelAdmin):
    #list_display=('initiative', 'A', 'B', 'C', 'D', 'E',)
    list_display=('initiative', 'proactive', 'proactiveType', 'likelyhoodAssetConsequence', 'severityJustification', 'likehoodJustification', 'mtoScore',)



admin.site.register(Formula_Level_1)
admin.site.register(Formula_Level_2)
admin.site.register(Formula_Level_3)
admin.site.register(Formula_Level_4)
admin.site.register(InfrastructureCategory)


@admin.register(ControlSequence)
class ControlSequenceAdmin(admin.ModelAdmin):
    list_display=('name', 'sequence_number', 'prefix')

@admin.register(InitiativeApprovals)
class InitiativeApprovalsAdmin(admin.ModelAdmin):
    list_display=('LGateId', 'comments', 'Created_Date', 'last_modified_date')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'uploaded_at')
    
    

# Create crontab schedule: Every Monday at 9 AM
schedule, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='9', day_of_week='1')

# # Schedule the task
# PeriodicTask.objects.create(
#     crontab=schedule,
#     name='Send Weekly Late Email',
#     task='your_app.tasks.send_weekly_late_items_email',
# )