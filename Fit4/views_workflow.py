from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import Initiative, Workstream
from Fit4.forms import *
from django.contrib import messages
from django.contrib.auth.models import User
import traceback
from django.contrib.auth import get_user_model
from user_visit.models import *
from enum import Enum
import datetime
from django.utils.timezone import now
from .notifications import *
from .views_advance_to_next_gate import *


#region ==================== Workflow starts here ========================

def workFlowStarts(request, oInitiative, o, oWorkstream):
    gate_index = o.actual_Lgate.GateIndex

    gate_handlers = {
        LGateIndex.L0.value: lambda: gateZero(request, o, oInitiative),
        LGateIndex.L1.value: lambda: gateOne(request, o, oInitiative, oWorkstream),
        LGateIndex.L2.value: lambda: gateTwo(request, o, oInitiative, oWorkstream),
        LGateIndex.L3.value: lambda: gateThree(request, o, oInitiative, oWorkstream),
        LGateIndex.L4.value: lambda: gateFour(request, o, oInitiative, oWorkstream),
        LGateIndex.L5.value: lambda: gateFive(request, o, oInitiative, oWorkstream),
    }

    handler = gate_handlers.get(gate_index)
    if handler:
        handler()
    else:
        raise ValueError(f"Unknown GateIndex: {gate_index}")

def gateZero(request, o, oInitiative):
    o.actual_Lgate = Actual_L_Gate.objects.get(GateIndex=LGateIndex.L1.value) # Change L Gate here. This will be the only place an initiative owner will change LGate, others will be changed on approval
    o.Planned_Date = o.L0_Completion_Date_Planned
    o.L0_Completion_Date_Actual = now() # Close Actual Completion Date for L0
    o.last_modified_by = request.user
    o.update =now()
    o.save()

    # Approval Request Submitted
    initiativeApprover = oInitiative.author
    submit_initiative_to_approver(oInitiative, LGateIndex.L1.value, "Approval Request Submitted", request.user, initiativeApprover)

def gateOne(request, o, oInitiative, oWorkstream):
    o.Planned_Date = o.L1_Completion_Date_Planned
    o.L1_Completion_Date_Actual = now() # Close Actual Completion Date for L1
    o.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Pending.value) # Change Approval Status Visual to Pending approval
    
    #Assign Workstream lead and Finance Sponsor to Initiative, if activate initiative approvers is false
    if not oInitiative.activate_initiative_approvers:
        o.workstreamlead = oWorkstream.user_workstreamlead
        o.financesponsor = oWorkstream.user_financesponsor
    
    # Approval Request Submitted
    initiativeApprover = oInitiative.author
    submit_initiative_to_approver(oInitiative, LGateIndex.L2.value, "Approval Request Submitted", request.user, initiativeApprover)
    #Assign Workstream Lead to Initiative_Approvals table at L2 approvals
    initiativeApprover = (oInitiative.workstreamlead if oInitiative.activate_initiative_approvers else oWorkstream.user_workstreamlead)
    assign_initiative_approver(oInitiative, LGateIndex.L2.value, "Workstream Lead", request.user, initiativeApprover)
    
    o.last_modified_by = request.user
    o.last_modified_date = now()
    o.save()
    
    messages.success(request, '<b>Initiative successfully sent for L2 approval.</b>') # message to show the initiative has been sent for L2 approval
    InitiativeOwnerSendmailToWorkStreamLead(request, oInitiative) #send mail to Workstream Lead

def gateTwo(request, o, oInitiative, oWorkstream):
    o.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Pending.value) # Approval Status Visual will change to Pending approval
        
    #Assign Workstream Lead, Workstream Sponsor and Finance Sponsor to Initiative
    if not oInitiative.activate_initiative_approvers:
        o.workstreamlead = oWorkstream.user_workstreamlead
        o.financesponsor = oWorkstream.user_financesponsor
        o.workstreamsponsor = oWorkstream.user_workstreamsponsor
    
    # Approval Request Submitted
    initiativeApprover = oInitiative.author
    submit_initiative_to_approver(oInitiative, LGateIndex.L3.value, "Approval Request Submitted", request.user, initiativeApprover)
    #Assign Workstream Lead to Initiative_Approvals table at L3 approvals
    initiativeApprover = (oInitiative.workstreamlead if oInitiative.activate_initiative_approvers else oWorkstream.user_workstreamlead)
    assign_initiative_approver(oInitiative, LGateIndex.L3.value, "Workstream Lead", request.user, initiativeApprover)
    
    o.last_modified_by = request.user
    o.last_modified_date = now()
    o.save()
    
    messages.success(request, '<b>Initiative successfully sent for L3 approval.</b>') # message to show the initiative has been sent for L3 approval
    InitiativeOwnerSendmailToWorkStreamLead(request, oInitiative) #send mail to Workstream Lead

def gateThree(request, o, oInitiative, oWorkstream):
    o.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Pending.value) # Approval Status Visual will change to Pending approval
        
    #Assign Workstream Lead and Finance Sponsor to Initiative
    if not oInitiative.activate_initiative_approvers:
        o.workstreamlead = oWorkstream.user_workstreamlead
        o.financesponsor = oWorkstream.user_financesponsor

    # Approval Request Submitted
    initiativeApprover = oInitiative.author
    submit_initiative_to_approver(oInitiative, LGateIndex.L4.value, "Approval Request Submitted", request.user, initiativeApprover)
    #Assign Workstream Lead to Initiative Approvals at L4 approvals
    initiativeApprover = (oInitiative.workstreamlead if oInitiative.activate_initiative_approvers else oWorkstream.user_workstreamlead)
    assign_initiative_approver(oInitiative, LGateIndex.L4.value, "Workstream Lead", request.user, initiativeApprover)
    
    o.last_modified_by = request.user
    o.last_modified_date = now()
    o.save()
    
    messages.success(request, '<b>Initiative successfully sent for L4 approval.</b>') # message to show the initiative has been sent for L4 approval
    InitiativeOwnerSendmailToWorkStreamLead(request, oInitiative) #send mail to Workstream Lead

def gateFour(request, o, oInitiative, oWorkstream):
    o.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Pending.value) # Approval Status Visual will change to Pending approval
        
    #Assign Finance Sponsor to Initiative
    if (oInitiative.activate_initiative_approvers == False):
        o.financesponsor = oWorkstream.user_financesponsor

    # Approval Request Submitted
    initiativeApprover = oInitiative.author
    submit_initiative_to_approver(oInitiative, LGateIndex.L5.value, "Approval Request Submitted", request.user, initiativeApprover)
    #Assign Finance Sponsor to Initiative Approvals table at L5 approval
    initiativeApprover = (oInitiative.financesponsor if oInitiative.activate_initiative_approvers else oWorkstream.user_financesponsor)
    assign_initiative_approver(oInitiative, LGateIndex.L5.value, "Finance Sponsor", request.user, initiativeApprover)
    
    o.last_modified_by = request.user
    o.last_modified_date = now()
    o.save()
    
    messages.success(request, '<b>Initiative successfully sent for L5 approval.</b>') # message to show the initiative has been sent for L5 approval
    #TODO send mail to Finance Sponsor
    WorkStreamLeadSendmailToFinanceSponsorCopyInitiativeOwner(request, oInitiative)

def gateFive(request, o, oInitiative, oWorkstream):
    o.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Pending.value) # Approval Status Visual will change to Pending approval
        
    #Assign Finance Sponsor to Initiative
    if not oInitiative.activate_initiative_approvers:
        o.financesponsor = oWorkstream.user_financesponsor

    # Approval Request Submitted
    initiativeApprover = oInitiative.author
    submit_initiative_to_approver(oInitiative, LGateIndex.L5.value, "Approval Request Submitted", request.user, initiativeApprover)

    #Assign Finance Sponsor to Initiative Approvals table at L5 approval
    initiativeApprover = (oInitiative.financesponsor if oInitiative.activate_initiative_approvers else oWorkstream.user_financesponsor)
    assign_initiative_approver(oInitiative, LGateIndex.L5.value, "Finance Sponsor", request.user, initiativeApprover)
    
    o.last_modified_by = request.user
    o.last_modified_date = now()
    o.save()
    
    messages.success(request, '<b>Initiative successfully sent for L5-Complete approval.</b>') # message to show the initiative has been sent for L5 approval
    #TODO send mail to Finance Sponsor
    InitiativeOwnerSendmailToFinanceSponsor(request, oInitiative)

def assign_initiative_approver(initiative, gate_index, role, user, initiativeApprover):
    gate = Actual_L_Gate.objects.get(GateIndex=gate_index)
    return InitiativeApprovals.objects.create(
        initiative=initiative,
        #status=ApprovalStatus.Submitted.value, This will be updated when an initiative is approved, rejected or reassigned.
        LGateId=gate,
        approver=initiativeApprover,
        actualApprover=initiativeApprover,
        created_by=user,
        Created_Date=now(),
        last_modified_by=user,
        rolePlayed=role
    )

def submit_initiative_to_approver(initiative, gate_index, role, user, initiativeApprover):
    gate = Actual_L_Gate.objects.get(GateIndex=gate_index)
    return InitiativeApprovals.objects.create(
        initiative=initiative,
        status=ApprovalStatus.Submitted.value,
        LGateId=gate,
        approver=initiativeApprover,
        actualApprover=initiativeApprover,
        created_by=user,
        Created_Date=now(),
        last_modified_by=user,
        rolePlayed=role
    )

#endregion =================== Workflow ends here ==========================


def approval_details(request, id):
    try:
        oApproval = InitiativeApprovals.objects.get(id=id)
        oApprovalForm = InitiativeApprovalsForm2(instance=oApproval)
        allUsers = get_user_model().objects.all()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'Fit4/Initiative/my_approval_details.html', {'oApproval': oApproval, 'oApprovalForm':oApprovalForm, 'allUsers':allUsers})


#1. Helper Functions
def create_approval(initiative, gate_index, approver, role, user):
    return InitiativeApprovals.objects.create(
        initiative=initiative,
        LGateId=Actual_L_Gate.objects.get(GateIndex=gate_index),
        approver=approver,
        actualApprover=approver,
        rolePlayed=role,
        created_by=user,
        Created_Date=now()
    )

def update_initiative_gate(initiative, gate_index, visual_status_id, completion_date_field):
    setattr(initiative, 'actual_Lgate', Actual_L_Gate.objects.get(GateIndex=gate_index))
    initiative.approval_status_visual = approvalStatusVisual.objects.get(id=visual_status_id)
    setattr(initiative, completion_date_field, now())
    initiative.Planned_Date = getattr(initiative, f"L{gate_index}_Completion_Date_Planned", None)
    initiative.save()

def finalize_approval(oApproval):
    oApproval.status = ApprovalStatus.Approved.value
    oApproval.save()

#2. Refactored Main Logic
def approve_initiative(request, id):
    try:
        oApproval = InitiativeApprovals.objects.get(id=id)
        oInitiative = Initiative.objects.get(id=oApproval.initiative.id)
        oImpact = InitiativeImpact.objects.filter(initiative=oInitiative)

        form = InitiativeApprovalsForm2(data=request.POST, instance=oApproval)
        o = form.save(commit=False)

        gate_index = oInitiative.actual_Lgate.GateIndex

        if gate_index == LGateIndex.L1.value:
            approve_initiative_at_gateIndex1(request, oApproval, oInitiative, o)
        elif gate_index == LGateIndex.L2.value:
            approve_initiative_at_gateIndex2(request, oApproval, oInitiative, o, oImpact)
        elif gate_index == LGateIndex.L3.value:
            approve_initiative_at_gateIndex3(request, oApproval, oInitiative, o)
        elif gate_index == LGateIndex.L4.value:
            approve_initiative_at_gateIndex4(request, oApproval, oInitiative, o)
        elif gate_index == LGateIndex.L5.value:
            approve_initiative_at_gateIndex5(request, oApproval, oInitiative, o)
    except Exception:
        print(traceback.format_exc())
    return render(request, 'Fit4/Initiative/my_approval_details.html', {'oApproval': oApproval})

def approve_initiative_at_gateIndex1(request, oApproval, oInitiative, o):
    if oApproval.approver == oInitiative.workstreamlead:
        next_approver = oInitiative.financesponsor if oInitiative.activate_initiative_approvers else oInitiative.Workstream.user_financesponsor
        create_approval(oInitiative, LGateIndex.L2.value, next_approver, "Finance Sponsor", request.user)
        finalize_approval(o)
        messages.success(request, 'Approved and sent for Finance Sponsor approval.')
        WorkStreamLeadSendmailToFinanceSponsorCopyInitiativeOwner(request, oInitiative)
    elif oApproval.approver == oInitiative.financesponsor:
        update_initiative_gate(oInitiative, LGateIndex.L2.value, ApprovalVisualStatus.Approved.value, "L2_Completion_Date_Actual")
        finalize_approval(o)
        messages.success(request, 'Initiative successfully approved.')
    return redirect('/en/home')

def approve_initiative_at_gateIndex2(request, oApproval, oInitiative, o, oImpact):
    if oApproval.approver == oInitiative.workstreamlead:
        next_approver = oInitiative.workstreamsponsor if oInitiative.activate_initiative_approvers else oInitiative.Workstream.user_workstreamsponsor
        create_approval(oInitiative, LGateIndex.L3.value, next_approver, "Workstream Sponsor", request.user)
        finalize_approval(o)
        messages.success(request, 'Approved and sent for Workstream Sponsor approval.')
        WorkStreamLeadSendmailToFinanceSponsorCopyInitiativeOwner(request, oInitiative)
    elif oApproval.approver == oInitiative.workstreamsponsor:
        next_approver = oInitiative.financesponsor if oInitiative.activate_initiative_approvers else oInitiative.Workstream.user_financesponsor
        create_approval(oInitiative, LGateIndex.L3.value, next_approver, "Finance Sponsor", request.user)
        finalize_approval(o)
        messages.success(request, 'Approved and sent for Finance Sponsor approval.')
    elif oApproval.approver == oInitiative.financesponsor:
        update_initiative_gate(oInitiative, LGateIndex.L3.value, ApprovalVisualStatus.Approved.value, "L3_Completion_Date_Actual")
        copyImpactPlanToForecast(oImpact)
        finalize_approval(o)
        messages.success(request, 'Initiative successfully approved.')
    return redirect('/en/home')

def approve_initiative_at_gateIndex3(request, oApproval, oInitiative, o):
    if oApproval.approver == oInitiative.workstreamlead:
        next_approver = oInitiative.financesponsor if oInitiative.activate_initiative_approvers else oInitiative.Workstream.user_financesponsor
        create_approval(oInitiative, LGateIndex.L4.value, next_approver, "Finance Sponsor", request.user)
        finalize_approval(o)
        messages.success(request, 'Approved and sent for Finance Sponsor approval.')
        WorkStreamLeadSendmailToFinanceSponsorCopyInitiativeOwner(request, oInitiative)
    elif oApproval.approver == oInitiative.financesponsor:
        update_initiative_gate(oInitiative, LGateIndex.L4.value, ApprovalVisualStatus.Approved.value, "L4_Completion_Date_Actual")
        finalize_approval(o)
        messages.success(request, 'Initiative successfully approved.')
    return redirect('/en/home')

def approve_initiative_at_gateIndex4(request, oApproval, oInitiative, o):
    if oApproval.approver == oInitiative.workstreamlead:
        next_approver = oInitiative.financesponsor if oInitiative.activate_initiative_approvers else oInitiative.Workstream.user_financesponsor
        create_approval(oInitiative, LGateIndex.L4.value, next_approver, "Finance Sponsor", request.user)
        finalize_approval(o)
        messages.success(request, 'Approved and sent for Finance Sponsor approval.')
        WorkStreamLeadSendmailToFinanceSponsorCopyInitiativeOwner(request, oInitiative)
    elif oApproval.approver == oInitiative.financesponsor:
        update_initiative_gate(oInitiative, LGateIndex.L5.value, ApprovalVisualStatus.Approved.value, "L5_Completion_Date_Actual")
        finalize_approval(o)
        messages.success(request, 'Initiative successfully approved.')
    return redirect('/en/home')

def approve_initiative_at_gateIndex5(request, oApproval, oInitiative, o):
    if oApproval.approver == oInitiative.financesponsor:
        update_initiative_gate(oInitiative, LGateIndex.L6.value, ApprovalVisualStatus.Approved.value, "L5_Completion_Date_Actual")
        finalize_approval(o)
        messages.success(request, 'Initiative successfully approved.')
    return redirect('/en/home')

# When an Initiative is approved at L3, update InitiativeImpact and copy all values in Plan to Forecast. Lock Plan and Open Forecast and Actual
def copyImpactPlanToForecast(oImpact):
    for o in oImpact:
        o.Jan_Forecast = o.Jan_Plan
        o.Feb_Forecast = o.Feb_Plan
        o.Mar_Forecast = o.Mar_Plan
        o.Apr_Forecast = o.Apr_Plan
        o.May_Forecast = o.May_Plan
        o.Jun_Forecast = o.Jun_Plan
        o.Jul_Forecast = o.Jul_Plan
        o.Aug_Forecast = o.Aug_Plan
        o.Sep_Forecast = o.Sep_Plan
        o.Oct_Forecast = o.Oct_Plan
        o.Nov_Forecast = o.Nov_Plan
        o.Dec_Forecast = o.Dec_Plan
        o.save()


def reject_initiative(request, id):
    try:
        oApproval = InitiativeApprovals.objects.get(id=id)
        oInitiative = Initiative.objects.get(id=oApproval.initiative.id)

        form = InitiativeApprovalsForm2(data=request.POST, instance=oApproval)
        o = form.save(commit=False)

        #Update Initiative status
        oInitiative.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Rejected.value)
        oInitiative.save()
        
        #Update Initiative Approval status
        o.status = ApprovalStatus.Rejected.value
        o.save()
        #TODO Send mail to Initiative owner
        return redirect('/en/approval_details/' + str(oApproval.id) + '/')
        
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'Fit4/Initiative/my_approval_details.html', {'oApproval': oApproval})

def reassign_initiative(request, id):
    try:
        selected_user_id = request.POST.get('selected_user')
        oApproval = InitiativeApprovals.objects.get(id=id)
        oInitiative = Initiative.objects.get(id=oApproval.initiative.id)

        form = InitiativeApprovalsForm2(data=request.POST, instance=oApproval)
        o = form.save(commit=False)

        #To who was it reassigned to?
        oApproval.actualApprover = User.objects.get(id=selected_user_id)
        oApproval.save()
        
        #Update Initiative Approval status
        o.status = ApprovalStatus.Reassigned.value
        o.save()
        #TODO Send mail to Initiative owner
        return redirect('/en/approval_details/' + str(oApproval.id) + '/')
        
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'Fit4/Initiative/my_approval_details.html', {'oApproval': oApproval})


class ApprovalVisualStatus(Enum):
    Approved = 1
    Pending = 2
    Recalled = 3
    Rejected = 4
    
class LGateIndex(Enum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    L6 = 6
    
class ApprovalStatus(Enum):
    Submitted = 1
    Rejected = 2
    Reassigned = 3
    Approved = 4
    Recalled = 5