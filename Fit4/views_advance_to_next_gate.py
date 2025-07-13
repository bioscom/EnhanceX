from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import Initiative, Workstream
from Fit4.forms import *
from django.contrib import messages
import traceback
from user_visit.models import *
from enum import Enum
from django.urls import reverse
from django.utils.timezone import now
from .notifications import *
from .views_workflow import *


def advance_to_next_LGate(request, id):
    try:
        oInitiative = Initiative.objects.get(id=id)
        oWorkstream = Workstream.objects.get(id=oInitiative.Workstream.id)
        if request.method == "POST" and request.user == oInitiative.author:
            form = InitiativeNextLGateForm(data=request.POST, instance=oInitiative)
            if form.is_valid():
                o = form.save(commit=False)
                
                # Check if Override Default Approvers roles are selected
                has_approver_roles = any([
                    oInitiative.workstreamsponsor is not None,
                    oInitiative.workstreamlead is not None,
                    oInitiative.financesponsor is not None
                ])

                # if roles are selected but Override Default approvers is not activated, warn the user
                if has_approver_roles and not oInitiative.activate_initiative_approvers:
                    messages.warning(request, '<b>Override Default Approvers</b> must be clicked.')
                    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
                
                # if roles are selected check if the approvers are in order
                if has_approver_roles:
                    if not validate_approvers_order(request, oInitiative):
                        return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

                # Validate if the selected dates are in order
                if not validate_date_order(request, o):
                    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

                # Validate initiative impact
                if o.actual_Lgate.GateIndex >= LGateIndex.L2.value:
                    impact_redirect = check_initiative_impact(request, id, oInitiative.slug)
                    if impact_redirect:
                        return impact_redirect

                workFlowStarts(request, oInitiative, o, oWorkstream)

                return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            messages.error(request, 'You do not have the right to progress initiative to Next LGate. You must be the Initiative Owner. Contact the Admin.')
            return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

def validate_approvers_order(request, initiative):
    if initiative.workstreamsponsor == initiative.workstreamlead:
        messages.warning(request, '<b>Workstream Sponsor cannot be the same as Workstream Lead</b>')
    elif initiative.financesponsor == initiative.workstreamlead:
        messages.warning(request, '<b>Finance Sponsor cannot be the same as Workstream Lead</b>')
    elif initiative.financesponsor == initiative.workstreamsponsor:
        messages.warning(request, '<b>Finance Sponsor cannot be the same as Workstream Sponsor</b>')
    elif initiative.author in [initiative.workstreamsponsor, initiative.workstreamlead, initiative.financesponsor]:
        messages.warning(request, '<b>Initiative Owner cannot be same as any approver</b>')
    else:
        return True  # All validations passed
    
    return False  # A warning was issued
#return True

# #TODO: kindly check this code. If no user is selected, it should not force user to select approvers
# def validate_approvers_activated(request, oInitiative):
#     #This is important when a user selects other users for approval other than the admin specific approvers in the system
#     if(oInitiative.workstreamsponsor or oInitiative.workstreamlead or oInitiative.financesponsor):
#         if (oInitiative.activate_initiative_approvers == False):
#             messages.warning(request, '<b>vActivate Initiative Approvers</b> must be clicked if you are selecting approvers other than the workstream specified approvers.')
#             return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

def validate_date_order(request, o):
    stages = [
        ('L0_Completion_Date_Planned', 'L1_Completion_Date_Planned'),
        ('L1_Completion_Date_Planned', 'L2_Completion_Date_Planned'),
        ('L2_Completion_Date_Planned', 'L3_Completion_Date_Planned'),
        ('L3_Completion_Date_Planned', 'L4_Completion_Date_Planned'),
        ('L4_Completion_Date_Planned', 'L5_Completion_Date_Planned'),
    ]

    for earlier, later in stages:
        earlier_date = getattr(o, earlier, None)
        later_date = getattr(o, later, None)

        if earlier_date is None:
            messages.warning(request, f'<b>({earlier.replace("_", " ")}) is missing. Please provide a date.</b>')
            return False

        if later_date is None:
            messages.warning(request, f'<b>({later.replace("_", " ")}) is missing. Please provide a date.</b>')
            return False

        if earlier_date > later_date:
            messages.warning(request, f'<b>Date error between ({earlier.replace("_", " ")}) and ({later.replace("_", " ")}). ({earlier.replace("_", " ")}) should be less or equal to ({later.replace("_", " ")}). Please review.</b>')
            return False

    return True

def check_initiative_impact(request, initiative_id, initiative_slug):
    if not InitiativeImpact.objects.filter(initiative=initiative_id).exists():
        messages.warning(request, '<b>Initiative Impact is required for G2 (Validate) Gate</b>')
        return redirect(reverse("Fit4:initiative_details", args=[initiative_slug]))
    return None



class ApprovalVisualStatus(Enum):
    Approved = 1
    Pending = 2
    Recalled = 3
    Rejected = 4

class ApprovalStatus(Enum):
    Submitted = 1
    Rejected = 2
    Reassigned = 3
    Approved = 4
    Recalled = 5
    
class LGateIndex(Enum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    L6 = 6