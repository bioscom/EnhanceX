from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import Initiative, Workstream
from django.contrib.auth.decorators import login_required
from Fit4.forms import *
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Count, Case, When, Value, IntegerField
import traceback
from user_visit.models import *
import datetime
from datetime import datetime
from django.core.mail import mail_admins
from django.utils.timezone import now
from django.urls import reverse
from .notifications import *
from django.db.models import Q, F, Prefetch

from .views_advance_to_next_gate import *
from .views_banner_mgt import *
from .views_mto import *
from .views_workstream import *
from .views_fcf_multiplier import *
from .views_initiative_mgt import *

def custom_server_error(request):
    # Capture error info
    #error_message = "A 500 error occurred.\n\n"
    #error_message += traceback.format_exc()

    # Send email to admins
    mail_admins(
        subject='500 Internal Server Error',
        message=f"Time: {now()}\nPath: {request.path}\nUser: {get_user_info(request)}\n",
        fail_silently=True # Avoid crashing if email fails
    )

    # Redirect to home
    return redirect("/en/home")

def custom_404_view(request, exception):
    mail_admins(
        subject='[Django] 404 Page Not Found',
        message=f"Time: {now()}\nPath: {request.path}\nUser: {get_user_info(request)}\n",
        fail_silently=True
    )
    return redirect("/en/home") # or render a custom error template

def custom_403_view(request, exception):
    mail_admins(
        subject='[Django] 403 Forbidden',
        message=f"Time: {now()}\nPath: {request.path}\nUser: {get_user_info(request)}\n",
        fail_silently=True
    )
    return redirect("/en/home")

def custom_400_view(request, exception):
    mail_admins(
        subject='[Django] 400 Bad Request',
        message=f"Time: {now()}\nPath: {request.path}\nUser: {get_user_info(request)}\n",
        fail_silently=True
    )
    return redirect("/en/home")

def get_user_info(request):
    return str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'AnonymousUser'



#region================================================= Search =================================================================================
# Note, this works using the htmx methods.
# Add the followings to the base.html template
# 1. <script src="https://unpkg.com/htmx.org@1.6.1/dist/htmx.min.js"></script>
# 2. <!-- MODAL POPUP PLACEHOLDER tabindex="-1"-->
#     <div id="modal" class="modal fade" data-bs-focus="false">
#      <div id="dialog" class="modal-dialog modal-lg" hx-target="this" style="overflow-y: initial !important">
#        <!-- inject HTML here -->
#      </div>
#    </div>
# 3. in the dialog.js file there is a JavaScript there to make the search show.
# The dialog.js file is not working right now, so I placed it on the base.html file, where it is working

#@login_required(login_url='account:login')
def search(request):
    searched = request.GET.get('search')
    if searched:
        results = Initiative.objects.filter(Q(initiative_name__icontains=searched) | Q(initiative_id__icontains=searched) | Q(oldinitiative_id__icontains=searched) | Q(author__first_name__icontains=searched) | Q(author__last_name__icontains=searched)).order_by('-Created_Date')
    else:
        results = []
    return render(request, "partials/partial_results.html", {"results": results})

#endregion ======================================================================================================================================

#region================================================ Home Page ================================================================================

@login_required(login_url='account:login_page')
def Home(request):
    initiatives = Initiative.objects.filter(author=request.user).filter(is_active=True, last_modified_date__year=datetime.datetime.today().year).order_by('-Created_Date')
    action_count = Initiative.objects.filter(author=request.user).filter(is_active=True, last_modified_date__year=datetime.datetime.today().year).annotate(action_count=Count('initiative_actions'))
    ZipInitiativeAction = zip(initiatives, action_count)
    
    initiativesCount = initiatives.count()
    form = InitiativeForm(request.POST)
    threatForm = InitiativeThreatForm(request.POST)
    
    oApprovals = InitiativeApprovals.objects.filter((Q(approver=request.user) | Q(actualApprover=request.user)) & Q(status = None)).exclude(Q(status=ApprovalStatus.Approved.value) | Q(status=ApprovalStatus.Rejected.value))
    noOfApprovals = oApprovals.count()

    oAction = Actions.objects.filter(assigned_to=request.user.id).exclude(status__name='Completed')
    noOfActions = oAction.count()

    banners = Banner.objects.filter(is_active=True).order_by('-uploaded_at')

    return render(request, 'Fit4/home.html', {'initiatives': initiatives, 'form': form, 'threatForm':threatForm, 
                                              'formAction':oAction, 'noOfActions':noOfActions, 'initiativesCount':initiativesCount, 
                                              'oApprovals':oApprovals, 'noOfApprovals':noOfApprovals, 'banners': banners, 'initiative':ZipInitiativeAction})
    
def recycleBin(request):
    initiatives = Initiative.objects.filter(author=request.user).filter(is_active=False).order_by('-Created_Date')
    action_count = Initiative.objects.filter(author=request.user).filter(is_active=False).annotate(action_count=Count('initiative_actions'))
    
    if request.user.is_superuser:
        initiatives = Initiative.objects.filter(is_active=False).order_by('-Created_Date')
        action_count = Initiative.objects.filter(is_active=False).annotate(action_count=Count('initiative_actions'))
        
    ZipInitiativeAction = zip(initiatives, action_count)
    
    initiativesCount = initiatives.count()
    form = InitiativeForm(request.POST)
    threatForm = InitiativeThreatForm(request.POST)
    
    # oApprovals = InitiativeApprovals.objects.filter((Q(approver=request.user) | Q(actualApprover=request.user)) & Q(status = None)).exclude(Q(status=ApprovalStatus.Approved.value) | Q(status=ApprovalStatus.Rejected.value))
    # noOfApprovals = oApprovals.count()

    oAction = Actions.objects.filter(assigned_to=request.user.id).exclude(status__name='Completed')
    noOfActions = oAction.count()

    return render(request, 'Fit4/Initiative/my_recycle_bin.html', {'initiatives': initiatives, 'form': form, 'threatForm':threatForm, 
                                              'formAction':oAction, 'noOfActions':noOfActions, 'initiativesCount':initiativesCount, 
                                               'initiative':ZipInitiativeAction})

def actions_list(request):
    workstreams = Workstream.objects.all()
    pendingActions = Actions.objects.filter(Created_Date__year=datetime.today().year).exclude(status__name='Completed').order_by('-start_date')
    completedActions = Actions.objects.filter(Q(Created_Date__year=datetime.today().year) & Q(status__name='Completed')).order_by('-start_date')
    return render(request, 'Fit4/Initiative/actions_report.html', {'pending': pendingActions, 'completed': completedActions, 'workstreams':workstreams})

def pending_approval(request):
    pendingApproval=InitiativeApprovals.objects.filter(Q(status=None) & Q(Created_Date__year=datetime.today().year)).order_by('-Created_Date')
    # o.status == None
    return render(request, 'Fit4/Initiative/pending_approval.html', {'pending': pendingApproval})

def initiatives_list(request):
    page_number = int(request.GET.get("page", 1))
    initiatives = Initiative.objects.all().order_by('-Created_Date')
    paginator = Paginator(initiatives, 100) # 50 records per page
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "next_page": page_number + 1 if page_obj.has_next() else None,
    }

    if request.htmx:
        return render(request, "partials/initiative_list_partial.html", context)
    return render(request, "Fit4/Initiative/initiative_list.html", context)

#endregion============================================== End Home Page ===========================================================================


#region================================================ Actions ===================================================================================

def add_actions(request, id):
    try:
        if request.method == "POST":
            oInitiative = Initiative.objects.get(id=id)
            form = ActionsForm(request.POST)
            if form.is_valid():
                oAction = form.save(commit=False)
                oAction.initiative = oInitiative
                oAction.created_by = request.user
                oAction.last_modified_by = request.user
                oAction.send_email = True
                oAction.save()
                #return HttpResponse(status=204, header={'HX-Trigger': 'change'} ) # No Content
                return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = ActionsForm()
    except Exception as e:
        print(traceback.format_exc())
        
    return render(request, "partials/partial_add_actions.html", {'form': form})

def action_details(request, id):  
    oAction = Actions.objects.get(id=id)
    actionForm = ActionsForm(instance=oAction)
    return render(request, 'Fit4/Initiative/actions_details.html', {'form':oAction, 'actionsForm':actionForm})

def edit_actions(request, id):
    try:
        oAction = Actions.objects.get(id=id)
        if request.method == "POST":
            form = ActionsForm(data=request.POST, instance=oAction)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                if (o.status == 'Completed'):
                    o.completion_date = datetime.date.now()
                o.save()
                return redirect('/en/actions_details/'+ str(id))
                #return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = ActionsForm(instance=oAction)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/actions_update.html", {'form': form})

#endregion============================================= End Actions ================================================================================

#region================================================ Members ===================================================================================

def add_member(request, id):
    try:
        if request.method == "POST":
            oInitiative = Initiative.objects.get(id=id)
            form = MemberForm(request.POST)
            if form.is_valid():
                oMember = form.save(commit=False)
                oMember.initiative = oInitiative
                oMember.created_by = request.user
                oMember.last_modified_by = request.user
                oMember.send_email = True
                oMember.save()
                #return redirect('/en/member_details/'+ str(oMember.id))
                return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = MemberForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_add_member.html", {'form': form})

def member_details(request, id): 
    oMember = TeamMembers.objects.get(id=id)
    memberForm = MemberForm(instance=oMember)
    return render(request, 'Fit4/Initiative/member_details.html', {'form':oMember, 'memberForm':memberForm})

def edit_member(request, id):
    try:
        oMember = TeamMembers.objects.get(id=id)
        if request.method == "POST":
            form = MemberForm(data=request.POST, instance=oMember)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()
                return redirect('/en/member_details/'+ str(id))
                #return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = MemberForm(instance=oMember)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/member_update.html", {'form': form})

#endregion============================================= End Members ================================================================================

#region================================================ Upload File ===============================================================================

def add_file(request, id):
    try:
        if request.method == "POST":
            oInitiative = Initiative.objects.get(id=id)
            form = FileForm(request.POST, request.FILES)
            if len(request.FILES) == 0:
                messages.error(request, '<b>No File Selected.</b>')
            else:
                if form.is_valid():
                #for f in files:
                    oFile = form.save(commit=False)
                    #oFile = add_file(initiativeFiles=f)
                    oFile.initiative = oInitiative
                    oFile.created_by = request.user
                    oFile.last_modified_by = request.user
                    oFile.save()
                    messages.success(request, '<b>1 file was added to the initiative.</b>')
            return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = FileForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_add_benefits.html", {'initiativeImpact': form})

#endregion=========================================================================================================================================

#region================================================ Add Notes =================================================================================

def add_note(request, id):
    try:
        if request.method == "POST":
            oInitiative = Initiative.objects.get(id=id)
            form = NoteForm(data=request.POST, files=request.FILES)
            if form.is_valid():
                o = form.save(commit=False)
                o.initiative = oInitiative
                o.created_by = request.user
                o.last_modified_by = request.user
                o.save()
                messages.success(request, '<b>Note Successfully added to the initiative.</b>')
                return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = FileForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_add_notes.html", {'initiativeImpact': form})

def edit_note(request, id):
    try:
        oInitiativeNote = InitiativeNotes.objects.get(id=id)
        oInitiative = Initiative.objects.get(id=oInitiativeNote.initiative)
        if request.method == "POST":
            form = NoteForm(data=request.POST, instance=oInitiativeNote)
            if form.is_valid():
                oNote = form.save(commit=False)
                oNote.last_modified_by = request.user
                oNote.save()
                messages.success(request, '<b>Note Successfully updated.</b>')
            return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = NoteForm(data=request.POST, instance=oInitiativeNote)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_edit_notes.html", {'form': form})

#endregion =========================================================================================================================================

#region ============================ Advance to Next L Gate refined ===========================

# def validate_date_order1(request, o):
#     stages = [
#         ('L0_Completion_Date_Planned', 'L1_Completion_Date_Planned'),
#         ('L1_Completion_Date_Planned', 'L2_Completion_Date_Planned'),
#         ('L2_Completion_Date_Planned', 'L3_Completion_Date_Planned'),
#         ('L3_Completion_Date_Planned', 'L4_Completion_Date_Planned'),
#         ('L4_Completion_Date_Planned', 'L5_Completion_Date_Planned'),
#     ]
#     for earlier, later in stages:
#         if getattr(o, earlier) > getattr(o, later):
#             messages.warning(request, f'<b>Date error between {earlier} and {later}. Please review.</b>')
#             return False
#     return True



# def advance_to_next_LGateNew(request, id):
#     oInitiative = get_object_or_404(Initiative, id=id)
#     oWorkstream = get_object_or_404(Workstream, id=oInitiative.Workstream.id)

#     if request.method != "POST" or request.user != oInitiative.author:
#         messages.error(request, 'You are not authorized to perform this action.')
#         return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

#     form = InitiativeNextLGateForm(data=request.POST, instance=oInitiative)
#     if not form.is_valid():
#         messages.error(request, 'Form validation failed.')
#         return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

#     o = form.save(commit=False)

    
#     has_approver_roles = any([
#         oInitiative.workstreamsponsor is not None,
#         oInitiative.workstreamlead is not None,
#         oInitiative.financesponsor is not None
#     ])

#     if has_approver_roles and not oInitiative.activate_initiative_approvers:
#         messages.warning(request, '<b>vActivate Initiative Approvers</b> must be clicked.')
#         return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
    
#     print("Sponsor:", oInitiative.workstreamsponsor)
#     print("Lead:", oInitiative.workstreamlead)
#     print("Finance:", oInitiative.financesponsor)

#     if not validate_date_order(request, o):
#         return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

#     try:
#         assign_approvers(o, oWorkstream)
#         gate_index = o.actual_Lgate.GateIndex

#         # Close previous stage
#         setattr(o, f'L{gate_index}_Completion_Date_Actual', now())
#         o.Planned_Date = getattr(o, f'L{gate_index}_Completion_Date_Planned')
#         o.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Pending.value)
#         o.last_modified_by = request.user
#         o.last_modified_date = now()

#         # Update next gate
#         if gate_index < LGateIndex.L5.value:
#             o.actual_Lgate = Actual_L_Gate.objects.get(GateIndex=gate_index + 1)

#         o.save()

#         # Log approvals
#         create_approval(oInitiative, gate_index + 1, "Approval Request Submitted", oInitiative.author)

#         approver = (
#             oInitiative.financesponsor if gate_index >= LGateIndex.L4.value
#             else oInitiative.workstreamlead if oInitiative.activate_initiative_approvers
#             else oWorkstream.user_workstreamlead
#         )
#         role = "Finance Sponsor" if gate_index >= LGateIndex.L4.value else "Workstream Lead"
#         create_approval(oInitiative, gate_index + 1, role, approver)

#         # Send mail based on stage
#         if gate_index == LGateIndex.L1.value:
#             InitiativeOwnerSendmailToWorkStreamLead(request, oInitiative)
#         elif gate_index == LGateIndex.L4.value:
#             WorkStreamLeadSendmailToFinanceSponsorCopyInitiativeOwner(request, oInitiative)
#         elif gate_index == LGateIndex.L5.value:
#             InitiativeOwnerSendmailToFinanceSponsor(request, oInitiative)

#         messages.success(request, f'<b>Initiative successfully sent for L{gate_index + 1} approval.</b>')
#         return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

#     except Exception as e:
#         print(traceback.format_exc())
#         messages.error(request, 'An error occurred. Please contact admin.')
#         return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

# def assign_approvers(initiative, workstream):
#     if not initiative.activate_initiative_approvers:
#         initiative.workstreamlead = workstream.user_workstreamlead
#         initiative.financesponsor = workstream.user_financesponsor
#         initiative.workstreamsponsor = getattr(workstream, 'user_workstreamsponsor', None)

#endregion ===================================================================================