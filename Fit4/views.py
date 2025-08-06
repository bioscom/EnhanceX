from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import Initiative, Workstream
from django.contrib.auth.decorators import login_required
from Fit4.forms import *
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Count, Case, When, Value, IntegerField, Min
import traceback
from user_visit.models import *
import datetime
from datetime import datetime
from django.core.mail import mail_admins
#from django.utils.timezone import now
from django.utils import timezone
from django.urls import reverse
from .notifications import *
from django.db.models import Q, F, Prefetch

from .views_advance_to_next_gate import *
from .views_banner_mgt import *
from .views_mto import *
from .views_workstream import *
from .views_fcf_multiplier import *
from .views_initiative_mgt import *
from .views_workflow import *

from dashboard.models import *

from django.db.models import Q, F, Prefetch, FloatField, ExpressionWrapper
from itertools import chain

from django.core.cache import cache

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

# @login_required(login_url='account:login_page')
# def Home(request):
#     current_year = now().year
#     today = now().date()
    
#     initiatives = Initiative.objects.filter(
#         author=request.user,
#         is_active=True, 
#         last_modified_date__year=current_year
#         ).annotate(
#             action_count=Count('initiative_actions')
#         ).select_related('overall_status').order_by('-Created_Date')
    
#     lateinitiatives = Initiative.objects.filter(
#         author=request.user,
#         is_active=True,
#         Planned_Date__lt=today
#     ).exclude(overall_status__name__in=['Completed', 'Cancelled', 'On hold', 'Defer']).order_by('-Created_Date')
    
#     show_late_modal = lateinitiatives.exists()

#     form = InitiativeForm(request.POST)
#     threatForm = InitiativeThreatForm(request.POST)

#     oApprovals = InitiativeApprovals.objects.filter(
#         Q(approver=request.user) | Q(actualApprover=request.user),
#         status=None
#     )

#     noOfApprovals = oApprovals.count()

#     oAction = Actions.objects.filter(
#         assigned_to=request.user
#     ).exclude(status__name='Completed')

#     noOfActions = oAction.count()

#     lateactions = oAction.filter(
#         due_date__lt=today
#     ).exclude(status__name='Cancelled')

#     show_late_actions = lateactions.exists()

#     banners = cache.get('active_banners')
#     if not banners:
#         banners = Banner.objects.filter(is_active=True).order_by('-uploaded_at')
#         cache.set('active_banners', banners, 300)

#     return render(request, 'Fit4/home.html', {
#         'initiatives': initiatives,
#         'formAddInitiative': form,
#         'threatForm': threatForm,
#         'formAction': oAction,
#         'noOfActions': noOfActions,
#         'initiativesCount': initiatives.count(),
#         'oApprovals': oApprovals,
#         'noOfApprovals': noOfApprovals,
#         'banners': banners,
#         'lateinitiatives': lateinitiatives,
#         'show_late_modal': show_late_modal,
#         'lateactions': lateactions,
#         'show_late_actions': show_late_actions
#     })
    
@login_required(login_url='account:login_page')
def Home(request):
    current_year = now().year
    today = now().date()
    
    # initiatives = Initiative.objects.filter(
    #     author=request.user,
    #     is_active=True, 
    #     last_modified_date__year=current_year
    #     ).annotate(
    #         action_count=Count('initiative_actions')
    #     ).select_related('overall_status').order_by('-Created_Date')
    
    # 1. First database entry
    initiatives = Initiative.objects.filter(
        author=request.user,
        is_active=True, 
        last_modified_date__year=current_year
    ).annotate(
        action_count=Count('initiative_actions'),
        earliest_due=Min('initiative_actions__due_date')
    ).order_by('-Created_Date')
    #action_count = initiatives.annotate(action_count=Count('initiative_actions'))
    #ZipInitiativeAction = zip(initiatives, action_count)

    lateinitiatives = Initiative.objects.filter(
        author=request.user,
        is_active=True,
        Planned_Date__lt=today
    ).exclude(overall_status__name__in=['Completed', 'Cancelled', 'On hold', 'Defer']).order_by('-Created_Date')
    
    #.exclude(overall_status__name='Completed').exclude(overall_status__name='Cancelled').exclude(overall_status__name='On hold').exclude(overall_status__name='Defer')

    show_late_modal = lateinitiatives.exists()
    
    form = InitiativeForm(request.POST)
    threatForm = InitiativeThreatForm(request.POST)
    
    # 2. Second database entry
    oApprovals = InitiativeApprovals.objects.filter(
        (Q(approver=request.user) | Q(actualApprover=request.user)) & Q(status = None)
    ).exclude(Q(status=ApprovalStatus.Approved.value) | Q(status=ApprovalStatus.Rejected.value))
    
    noOfApprovals = oApprovals.count()

    # 3. Third database entry
    allActions = Actions.objects.all()
    oAction = allActions.filter(
        assigned_to=request.user.id
    ).exclude(status__name='Completed')
    noOfActions = oAction.count()
    
    lateactions = allActions.filter(
        assigned_to=request.user.id, 
        due_date__lt=today
    ).exclude(status__name__in=['Completed', 'Cancelled'])
    
    show_late_actions = lateactions.exists()

    # 4. Fourth database entry
    banners = Banner.objects.filter(is_active=True).order_by('-uploaded_at')

    return render(request, 'Fit4/home.html', {
        'initiatives': initiatives, 
        'formAddInitiative': form, 
        'threatForm':threatForm, 
        'formAction':oAction, 
        'noOfActions':noOfActions, 
        'initiativesCount':initiatives.count(), 
        'oApprovals':oApprovals, 
        'noOfApprovals':noOfApprovals, 
        'banners': banners, 
        #'initiative':ZipInitiativeAction, 
        'lateinitiatives':lateinitiatives, 
        'show_late_modal': show_late_modal,
        'lateactions': lateactions, 
        'show_late_actions': show_late_actions,
        'today':today,
    })

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
    pendingActions = Actions.objects.filter(Created_Date__year=now().year).exclude(status__name='Completed').order_by('-start_date')
    completedActions = Actions.objects.filter(Q(Created_Date__year=now().year) & Q(status__name='Completed')).order_by('-start_date')
    return render(request, 'Fit4/Initiative/actions_report.html', {'pending': pendingActions, 'completed': completedActions, 'workstreams':workstreams})

def pending_approval(request):
    pendingApproval=InitiativeApprovals.objects.filter(Q(status=None) & Q(Created_Date__year=now().year)).order_by('-Created_Date')
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
    return render(request, 'Fit4/Initiative/actions_details.html', {'action':oAction, 'form':actionForm})

def edit_actions(request, id):
    try:
        oAction = Actions.objects.get(id=id)
        if request.method == "POST":
            form = ActionsForm(data=request.POST, instance=oAction)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                if (o.status == 'Completed'):
                    o.completion_date = now()
                o.save()
                return redirect('/en/actions_details/'+ str(id))
                #return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = ActionsForm(instance=oAction)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/actions_update.html", {'form': form})

def delete_action(request, id):
    o = Actions.objects.get(id=id)
    oInitiative = Initiative.objects.get(id=o.initiative.id)
    # Check if the user is the owner of the action
    try:
        if request.method == "POST":
            if request.user == o.assigned_to or request.user == o.created_by:
                o.delete()
                messages.success(request, '<b>'+ o.action_name + '</b> successfully deleted.')
            else:
                messages.error(request, 'You are not authorized to delete this action.')
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

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

#region================================================ Asset Heirarchy =============================================================================

def get_level2(request):
    level1_id = request.GET.get('level1_id')
    options = Formula_Level_2.objects.filter(formula_Level_1=level1_id).values('id', 'name')
    html = render_to_string('partials/option_list.html', {'options': options})
    return JsonResponse({'options': html})

def get_level3(request):
    level2_id = request.GET.get('level2_id')
    options = Formula_Level_3.objects.filter(formula_Level_2=level2_id).values('id', 'name')
    html = render_to_string('partials/option_list.html', {'options': options})
    return JsonResponse({'options': html})

def get_level4(request):
    level3_id = request.GET.get('level3_id')
    options = Formula_Level_4.objects.filter(formula_Level_3=level3_id).values('id', 'name')
    html = render_to_string('partials/option_list.html', {'options': options})
    return JsonResponse({'options': html})

#endregion =========================================================================================================================================