from simple_salesforce import Salesforce
from django.conf import settings
from Fit4.models import *


def connect_salesforce():
    try:
        return Salesforce(
            username=settings.SALESFORCE_USERNAME, 
            password=settings.SALESFORCE_PASSWORD, 
            security_token=settings.SALESFORCE_SECURITY_TOKEN,
            client_id=settings.SALESFORCE_CLIENT_ID
        )
    except Exception as e:
        # Handling connection errors
        print(f"Salesforce connection setup error: {str(e)}")
        return None
    
def fetch_salesforce_report(report_id):
    sf = connect_salesforce()
    
    if sf is None:
        # If there's an issue with the sf connection, return an error or raise exception.
        return "Salesforce connection setup error"
    try:
        ## use query_more to pull the complete results. Must pass True if using URL
        # query_result = sf.query_more(f"/services/data/v57.0/analytics/reports/{report_id}", True)
        # return query_result
        report_data = sf.restful(f"analytics/reports/{report_id}")
        return report_data
    except Exception as e:
        # Handle query errors here
        print(f"Salesforce query error: {str(e)}")
        return None

def push_django_data_to_salesforce():
    sf = connect_salesforce()
    records = get_django_data_for_salesforce()
    for record in records:
        sf.CustomObject__c.create(record)

def get_django_data_for_salesforce():
    records = []
    for record in Initiative.objects.all():
        records.append({'Initiative_name': record.initiative_name,
                        'Id': record.initiative_id,
                        'WorkStream': record.Workstream,
                        'Actual_LGate': record.actual_Lgate,
                        'overall_status': record.overall_status,
                        'slug': record.slug,
                        'approval_status_visual': record.approval_status_visual,
                        'next_LGate_Comment': record.next_Lgate_Comment,
                        'Initiative_Owner': record.author,
                        'Description': record.description, 
                        'problem_statement': record.problem_statement,
                        'OverallStatusCommentary': record.overallstatuscommentary,
                        'Discipline': record.discipline,
                        'Function': record.Function,
                        'SavingType': record.SavingType,
                        'WorkStreamSponsor': record.workstreamsponsor,
                        'WorkStreamLead': record.workstreamlead,
                        'FinanceSponsor': record.financesponsor,
                        'InitiativeSponsor': record.initiativesponsor,
                        'Yearly_Planned_Value': record.Yearly_Planned_Value,
                        'Yearly_Forecast_Value': record.Yearly_Forecast_Value,
                        'Yearly_Actual_value': record.Yearly_Actual_value,
                        'EnabledBy': record.enabledby,
                        'Plan_Relevance': record.Plan_Relevance,
                        'L0_Completion_Date_Planned': record.L0_Completion_Date_Planned.isoformat(),
                        'L1_Completion_Date_Planned': record.L1_Completion_Date_Planned.isoformat(),
                        'L2_Completion_Date_Planned': record.L2_Completion_Date_Planned.isoformat(),
                        'L3_Completion_Date_Planned': record.L3_Completion_Date_Planned.isoformat(),
                        'L4_Completion_Date_Planned': record.L4_Completion_Date_Planned.isoformat(),
                        'L5_Completion_Date_Planned': record.L5_Completion_Date_Planned.isoformat(),
                        'L0_Completion_Date_Actual': record.L0_Completion_Date_Actual.isoformat(),
                        'L1_Completion_Date_Actual': record.L1_Completion_Date_Actual.isoformat(),
                        'L2_Completion_Date_Actual': record.L2_Completion_Date_Actual.isoformat(),
                        'L3_Completion_Date_Actual': record.L3_Completion_Date_Actual.isoformat(),
                        'L4_Completion_Date_Actual': record.L4_Completion_Date_Actual.isoformat(),
                        'L5_Completion_Date_Actual': record.L5_Completion_Date_Actual.isoformat(),
                        'Planned_Date': record.Planned_Date.isoformat(),
                        'Approval_Status': record.Approval_Status,
                        'HashTag': record.HashTag, 
                        'Created_Date': record.Created_Date.isoformat(),
                        'updated': record.updated,
                        'mark_as_confidential': record.mark_as_confidential,
                        'DocumentLink': record.DocumentLink,
                        'SharepointUrl': record.SharepointUrl,
                        'YYear': record.YYear,
        })
    return records



        

# def get_django_data_for_salesforce():
#     records = []
#     for record in Initiative.objects.all():
#         records.append({
#             'Name': record.initiative_name,
#             'Amount__c': record.amount,
#             'Date__c': record.date.isoformat()
#         })
#     return records