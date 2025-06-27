import json
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.http import HttpResponseBadRequest
from .models import Initiative, Workstream
from django.contrib.auth.decorators import login_required
from Fit4.forms import *
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import random
import string
from django.db.models import Q, Count, Case, When, Value, IntegerField
import traceback
import logging
from django.contrib.auth import get_user_model
from user_visit.models import *
from enum import Enum
import datetime
from datetime import datetime
from django.http import JsonResponse
from smtplib import SMTPException
from django.core.mail import send_mail, EmailMultiAlternatives
from Fit4.tables import InitiativeTable
from django.db import transaction
from django.forms import modelformset_factory
import os
from django.template.loader import get_template
import pandas as pd
from django.core.mail import mail_admins
from django.utils.timezone import now
from django.urls import reverse
from .notifications import *
from django.views.decorators.csrf import csrf_exempt
from itertools import zip_longest
from django.db.models import Q, F, Prefetch


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


#region================================================= Banner Management =================================================================================

#@login_required(login_url='account:login')
def banner_list(request):
    try:
        banner_formset=[]
        bannerForm = BannerForm(request.POST)
        banners = Banner.objects.filter().order_by('-uploaded_at')
        for o in banners:
            banner_formset.append(BannerForm(instance=o))

        Zipformsets = zip(banners, banner_formset)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'Fit4/upload_banner.html', {'form': bannerForm, 'bannerFormset':Zipformsets})


#@login_required(login_url='account:login')
def add_banner(request):
    try:
        #banners = Banner.objects.filter().order_by('-uploaded_at')
        if request.method == 'POST':
            form = BannerForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect('/en/banners/')
        else:
            form = BannerForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'Fit4/upload_banner.html', {'form': form})


#@login_required(login_url='account:login')
def update_banner(request, id):
    try:  
        banner = Banner.objects.filter(id=id).first()
        if request.method == "POST":
            formBanner = BannerForm(data=request.POST, files=request.FILES, instance=banner)
            if formBanner.is_valid():
                formBanner.save()
                # o = form.save(commit=False)
                # o = form.save()
                return redirect('/en/banners/')
        else:
            formBanner = BannerForm(instance=banner)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/upload_banner.html", {'formBanner': formBanner, 'banners':banner})

#@login_required(login_url='account:login')
def delete_banner(request, id):
    banner = Banner.objects.filter(id=id).first()
    try:
        banner.delete()
        messages.success(request, '<b>'+ banner.title + '</b> successfully deleted.')
        return redirect('/en/banners/')
    except Exception as e:
        print(traceback.format_exc())
    return redirect('/en/banners/')

#endregion=========================================================================================================================================

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

#region================================================= WorkStream =============================================================================

#@login_required(login_url='account:login')
def update_predefinedApprovers(request, id):
    try:
        oApprover = PredefinedApprovers.objects.get(id=id)
        if request.method == "POST":
            form = PredefinedApproversForm(request.POST, instance=oApprover)
            if form.is_valid():
                Lgate = form.save(commit=False)
                Lgate.last_modified_by = request.user
                Lgate.save()
                
                return redirect("/en/approvers/" + str(oApprover.id) + "/view")
        else:
            form = PredefinedApproversForm(instance=oApprover)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/Workstream/PredefinedApproversDetails.html", {'form': form, 'approvers':oApprover})

#@login_required(login_url='account:login')
def workstream_List(request):
    oWorkStream = Workstream.objects.all()
    workStreamForm = WorkStreamForm(request.POST)
    return render(request, 'Fit4/Workstream/workstream_list.html', {'workstreams': oWorkStream, 'workstreamform':workStreamForm})

#@login_required(login_url='account:login')
def add_workstream(request):
    try:
        if request.method == "POST":
            form = WorkStreamForm(request.POST)
            if form.is_valid():
                oWorkStream = form.save(commit=False)
                oWorkStream.author = request.user
                oWorkStream.created_by = request.user
                oWorkStream.last_modified_by = request.user
                oWorkStream.save()

                create_predefinedApproversLgate(request=request, oWorkstream=oWorkStream)
                messages.success(request, '<b>'+ oWorkStream.workstreamname + '</b> successfully created.')
                return redirect('/en/workstream')
        else:
            form = WorkStreamForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_add_workstream.html", {'form': form})

def create_predefinedApproversLgate(request, oWorkstream):
    oActualLgate = Actual_L_Gate.objects.all()
    for o in oActualLgate:
        PredefinedApprovers.objects.create(
            Workstream=oWorkstream, 
            actual_Lgate=o, 
            created_by=request.user,
            last_modified_by=request.user)
    return None

@login_required(login_url='account:login_page')
def workstream_details(request, slug):
    oWorkstream = Workstream.objects.get(slug=slug)
    oPredefinedApprovers = PredefinedApprovers.objects.filter(Workstream=oWorkstream.id)
    workstreamform = WorkStreamForm(instance=oWorkstream)
    workstreamHierarchyform = WorkstreamAssetHierarchyForm(instance=oWorkstream)
    
    allUsers = User.objects.all()
    
    initiatives = Initiative.objects.filter(Workstream = oWorkstream)
    initCount = initiatives.count()
    return render(request, 'Fit4/Workstream/workstream_details.html', {'form':oWorkstream, 'workstreamform':workstreamform, 'initiatives':initiatives, 'initCount':initCount, 'allUsers':allUsers, 'oApprovers':oPredefinedApprovers, 'assethierarchyForm':workstreamHierarchyform})

#@login_required(login_url='account:login')
def edit_workstream(request, slug):
    try:
        oWorkstream = Workstream.objects.get(slug=slug)
        if request.method == "POST":
            form = WorkStreamForm(data=request.POST, instance=oWorkstream)
            if form.is_valid():
                oWorkstream.last_modified_by = request.user
                oWorkstream = form.save()
                return redirect('/en/wsdetails/'+ slug)
                #return HttpResponse(status=204)
        else:
            form = WorkStreamForm(instance=oWorkstream)
    except Exception as e:
        print(traceback.format_exc())
    return redirect('/en/wsdetails/'+ slug)
    #return render(request, "partials/partial_edit_initiative.html", { 'form': form })

#@login_required(login_url='account:login')
def delete_workstream(request, id):
    o = Workstream.objects.get(id=id)
    if request.method == "POST":
        if request.user == o.author:
            #TODO: Kindly put this on suspension, as deleting a workstream could delete an entire initiatives in the workstream. Delete a workstream should archive it.
            #o.delete()
            messages.success(request, '<b>'+ o.workstreamname + '</b> successfully deleted.')
            return redirect('/en/workstream')
    return render(request, 'Fit4/Initiative_List.html', {'posts': o})

#@login_required(login_url='account:login')
def update_workstream_assethierarchy(request, slug):
    try:
        oWorkstream = Workstream.objects.get(slug=slug)
        if request.method == "POST":
            form = WorkstreamAssetHierarchyForm(data=request.POST, instance=oWorkstream)
            if form.is_valid():
                o = form.save(commit=False)       
                o = form.save()
                return redirect('/en/wsdetails/'+ slug)

                #return HttpResponse( status=204, headers={ 'HX-Trigger': json.dumps({ "initiativeChanged": None, "showMessage": f"{oInitiative.initiative_name} successfully updated." })})
                #return redirect('/en/wsdetails/'+ slug)
        else:
            form = WorkstreamAssetHierarchyForm(instance=oWorkstream)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/Workstream/workstream_details.html", { 'initiativeForm': form, 'workstream':oWorkstream })  

#endregion========================================================================================================================================

#region================================================ Home Page ================================================================================

@login_required(login_url='account:login_page')
def Home(request):
    initiatives = Initiative.objects.filter(author=request.user).filter(is_active=True, last_modified_date__year=datetime.today().year).order_by('-Created_Date')
    action_count = Initiative.objects.filter(author=request.user).filter(is_active=True, last_modified_date__year=datetime.today().year).annotate(action_count=Count('initiative_actions'))
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


# @login_required(login_url='account:login')
# def LLinitiatives_list(request):
#     initiatives = Initiative.objects.all().order_by('-Created_Date')
#     form = InitiativeForm(request.POST)
#     return render(request, 'Fit4/Initiative/initiatives.html', {'initiatives': initiatives, 'form': form})

#@login_required(login_url='account:login')
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

# @login_required(login_url='account:login')
# def oInitiatives_list(request):
#     initiatives = Initiative.objects.all()
#     return render(request, 'Fit4/all_Initiatives.html', {'initiatives': initiatives})

#endregion============================================== End Home Page ===========================================================================

#region =============================================== Initiatives ==============================================================================

#@login_required(login_url='account:login_page')
def add_initiative(request):
    try:
        if request.method == "POST":
            form = InitiativeForm(request.POST)
            if form.is_valid():
                oInitiative = form.save(commit=False)
                oInitiative.author = request.user
                oInitiative.initiative_id = ControlSequence.get_next_number('R') #"R-" + create_object()
                oInitiative.YYear = datetime.now().year
                oInitiative.currency = Currency.objects.get(title='US Dollar')
                oInitiative.recordType = record_type.objects.get(name='Opportunity')
                oInitiative.last_modified_by = request.user
                oInitiative.created_by = request.user
                oInitiative.save()
                return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = InitiativeForm()
    except Exception as e:
        print(traceback.format_exc())        
    return render(request, "partials/partial_add_initiative.html", {'form': form})

def clone_initiative(request):
    try:
        if request.method == "POST":
            form = InitiativeForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.author = request.user
                o.initiative_id = ControlSequence.get_next_number('R') #"R-" + create_object()
                o.initiative_name = "#[Cloned from] " + request.POST.get("initiative_name")
                o.YYear = datetime.now().year
                o.currency = Currency.objects.get(title='US Dollar')
                o.recordType = record_type.objects.get(name='Opportunity')
                o.actual_Lgate = Actual_L_Gate.objects.get(GateIndex=LGateIndex.L0.value)
                o.overall_status = overall_status.objects.first()
                o.last_modified_by = request.user
                o.created_by = request.user
                
                o.save()
                return redirect(reverse("Fit4:initiative_details", args=[o.slug]))
        else:
            form = InitiativeForm()
    except Exception as e:
        print(traceback.format_exc())        
    return render(request, "partials/partial_clone_initiative.html", {'form': form})

#@login_required(login_url='account:login_page')
def add_threat(request):
    try:
        if request.method == "POST":
            form = InitiativeThreatForm(request.POST)
            if form.is_valid():
                oInitiative = form.save(commit=False)
                oInitiative.author = request.user
                oInitiative.initiative_id = ControlSequence.get_next_number('R') #"R-" + create_object()
                oInitiative.YYear = datetime.now().year
                oInitiative.currency = Currency.objects.get(title='US Dollar')
                oInitiative.recordType = record_type.objects.get(name='Threat')
                oInitiative.last_modified_by = request.user
                oInitiative.created_by = request.user
                oInitiative.save()

                return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = InitiativeThreatForm()
    except Exception as e:
        print(traceback.format_exc())
        
    return render(request, "partials/partial_add_threat.html", {'form': form})


def clone_MTO_initiative(request, slug):
    try:
        if request.method == "POST":
            form = InitiativeThreatForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.author = request.user
                o.initiative_id = ControlSequence.get_next_number('R') #"R-" + create_object()
                o.YYear = datetime.now().year
                o.currency = Currency.objects.get(title='US Dollar')
                o.recordType = record_type.objects.get(name='Threat')
                o.last_modified_by = request.user
                o.created_by = request.user
                o.save()

                return redirect(reverse("Fit4:initiative_details", args=[o.slug]))
        else:
            form = InitiativeThreatForm()
    except Exception as e:
        print(traceback.format_exc())
        
    return render(request, "partials/partial_clone_threat.html", {'form': form})

#@login_required(login_url='account:login_page')
def update_AssetHierarchy(request, slug):
    try:
        oInitiative = Initiative.objects.get(slug=slug)
        oWorkstream = Workstream.objects.get(id=oInitiative.Workstream.pk)
        if request.method == "POST":
            form = AssetHierarchyForm(data=request.POST, instance=oInitiative)
            if form.is_valid():
                o = form.save(commit=False)
                #oInitiative.currency = Currency.objects.get(title='US Dollar')
                #oInitiative.YYear = datetime.now().year
                if (validate(request, o) != None):
                    # messages.warning(request, '<b>The date inputted, should be greater or equal to the date captured in the previous stage. Review the Completion Date (Planned)</b>')
                    #return redirect('/initiative/' + slug)
                    return redirect(reverse("Fit4:initiative_details", args=[slug]))
                o = form.save()

                #return HttpResponse( status=204, headers={ 'HX-Trigger': json.dumps({ "initiativeChanged": None, "showMessage": f"{oInitiative.initiative_name} successfully updated." })})
                return redirect(reverse("Fit4:initiative_details", args=[slug]))
        else:
            form = AssetHierarchyForm(instance=oInitiative)
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[slug]))
    #return render(request, "Fit4/edit_initiative.html", { 'initiativeForm': form, 'initiative':oInitiative, 'workstream':oWorkstream })  

#@login_required(login_url='account:login_page')
def edit_initiative(request, slug):
    try: 
        oInitiative = Initiative.objects.get(slug=slug)
        oWorkstream = Workstream.objects.get(id=oInitiative.Workstream.pk)
        if request.method == "POST":
            if request.user.is_superuser:
                form = InitiativeForm2(data=request.POST, instance=oInitiative)
            else: 
                form = InitiativeForm2Users(data=request.POST, instance=oInitiative)
            
            if form.is_valid():
                o = form.save(commit=False)
                o.currency = Currency.objects.get(title='US Dollar')
                o.YYear = datetime.now().year
                o.last_modified_by = request.user
                if validate(request, o) is not None:
                    # messages.warning(request, '<b>The date inputted, should be greater or equal to the date captured in the previous stage. Review the Completion Date (Planned)</b>')
                    #return redirect('/initiative/' + slug)
                    return redirect(reverse("Fit4:initiative_details", args=[slug]))
                o.save()
                form.save_m2m()
                # Call on Init_Details.html
                #return HttpResponse( status=204, headers={'HX-Trigger': json.dumps({ "initiativeChanged": None,  "showMessage": f"{oInitiative.initiative_name} successfully updated." })}) 
                return redirect(reverse("Fit4:initiative_details", args=[slug]))
        else:
            form = InitiativeForm2(instance=oInitiative)
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[slug]))
    #return render(request, "Fit4/edit_initiative.html", { 'initiativeForm': form, 'initiative':oInitiative, 'workstream':oWorkstream })

def validate(request, o):
    # Validate the dates that L0 is not earlier that L1 and so on
    if (o.L0_Completion_Date_Planned == None or o.L1_Completion_Date_Planned == None or o.L2_Completion_Date_Planned == None or o.L3_Completion_Date_Planned == None or o.L4_Completion_Date_Planned == None or o.L5_Completion_Date_Planned == None):
        return messages.warning(request, '<b>Ensure all Planned dates are inputted, and next date should be greater or equal to the date captured in the previous stage</b>')

    if(o.L0_Completion_Date_Planned != None and o.L1_Completion_Date_Planned !=None and o.L2_Completion_Date_Planned !=None and o.L3_Completion_Date_Planned !=None and o.L4_Completion_Date_Planned !=None and o.L5_Completion_Date_Planned !=None):
        if (o.L0_Completion_Date_Planned > o.L1_Completion_Date_Planned):
            return messages.warning(request, '<b>The date inputted, should be greater or equal to the date captured in the previous stage Review L1 Completion Date (Plan)</b>')
        elif (o.L1_Completion_Date_Planned > o.L2_Completion_Date_Planned):
            return messages.warning(request, '<b>The date inputted, should be greater or equal to the date captured in the previous stage Review L2 Completion Date (Plan)</b>')
        elif (o.L2_Completion_Date_Planned > o.L3_Completion_Date_Planned):
            return messages.warning(request, '<b>The date inputted, should be greater or equal to the date captured in the previous stage Review L3 Completion Date (Plan)</b>')
        elif (o.L3_Completion_Date_Planned > o.L4_Completion_Date_Planned):
            return messages.warning(request, '<b>The date inputted, should be greater or equal to the date captured in the previous stage Review L4 Completion Date (Plan)</b>')
        elif (o.L4_Completion_Date_Planned > o.L5_Completion_Date_Planned):
            return messages.warning(request, '<b>The date inputted, should be greater or equal to the date captured in the previous stage Review L5 Completion Date (Plan)</b>')
    return None

#@login_required(login_url='account:login_page')
def edit_DocsLinks(request, id):
    try:
        oInitiative = Initiative.objects.get(id=id)
        if request.method == "POST":
            form = InitiativeForm3(data=request.POST, instance=oInitiative)
            if form.is_valid():
                oInitiative = form.save()
                return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = InitiativeForm3(instance=oInitiative)
    except Exception as e:
        print(traceback.format_exc())
        
    return render(request, "partials/partial_edit_documents.html", { 'form': form })

#@login_required(login_url='account:login_page')
def delete_initiative(request, id):
    try:
        post = Initiative.objects.get(id=id)
        if request.method == "POST":
            if request.user == post.author:
                post.is_active = False
                post.save()
                print("is_active set to False and saved")
                messages.success(request, '<b>'+ post.initiative_name + '</b> successfully deleted.')
                return redirect('/en/home')
    except Exception as e:
        print("Save failed:", e)
    return render(request, 'Fit4/Initiative_List.html', {'posts': post})


def initiative_details(request, slug):
    try:
        if slug == '...':
            return HttpResponseBadRequest("Invalid initiative slug.")

        oInitiative = get_object_or_404(Initiative, slug=slug)
        allUsers = get_user_model().objects.all()
        oProactiveType = ProactiveType.objects.all()
        oThreatlikelihood = ThreatLikelihood.objects.all()

        unitImpact = UnitImpactEntry.objects.filter(initiative=oInitiative)

        if oInitiative.unit:
            oUnit = Unit.objects.filter(
                Q(active=True) | Q(pk=oInitiative.unit.pk)
                ).annotate(
                    is_selected=Case(
                        When(id=oInitiative.unit.pk, then=Value(0)), 
                        default=Value(1), 
                        output_field=IntegerField()
                    )
                ).order_by('is_selected', 'name')
                
            if not unitImpact.exists():
                impact_entry(request, oUnit, slug)
        else:
            oUnit = Unit.objects.all()

        unitImpact = UnitImpactEntry.objects.filter(initiative=oInitiative)
        ZipUnits = zip_longest(oUnit, unitImpact, fillvalue=None)

        oPlanRelevance = oInitiative.Plan_Relevance.all()
        oEnabledBy = oInitiative.enabledby.all() 
        initiativeForm = InitiativeForm2(instance=oInitiative)
        initiativeForm3 = InitiativeForm3(instance=oInitiative)
        assetHierarchyForm = AssetHierarchyForm(instance=oInitiative)
        initiativeThreatForm = InitiativeThreatForm(instance=oInitiative)
        initiativeNextLGateForm = InitiativeNextLGateForm(instance=oInitiative)
        mtoScoringForm = MTOScoringForm(instance=oInitiative)
        mtoScoringInfoForm = MTOScoringInfoForm(instance=oInitiative)
        riskAssessmentForm = MTORiskAssessmentForm(instance=oInitiative)

        # Continue processing forms and related objects...

        initiatives_formset = []
        allInitiativesByWorkstream = Initiative.objects.filter(Workstream = oInitiative.Workstream)
        for o in allInitiativesByWorkstream:
                initiatives_formset.append(InitiativesByWorkstreamForm(instance=o))
        
        oWorkstream = get_object_or_404(Workstream, id=oInitiative.Workstream.pk)
        benefitType = BenefitTypeForm(request.POST)

        current_year = datetime.now().year
        initiativeImpactForm = InitiativeImpactForm(request.POST, initial={'YYear':current_year})
        
        initiativeImpact = []
        impact_formset = []
        if InitiativeImpact.objects.filter(initiative=oInitiative.id).exists():
            initiativeImpact = InitiativeImpact.objects.filter(initiative=oInitiative.id).order_by('-YYear')
            for o in initiativeImpact:
                impact_formset.append(InitiativeImpactForm(instance=o))
        else:
            initiativeImpact = []
            impact_formset = []
            
        Zipformsets = zip(initiativeImpact, impact_formset)

        
        oActions = Actions.objects.filter(initiative=oInitiative.id)
        actionsForm = ActionsForm(request.POST)
        #editActionsForm = ActionsForm(instance=oActions)
        noOfActions = oActions.count()
        
        oMembers = TeamMembers.objects.filter(initiative=oInitiative.id)
        membersForm = MemberForm(request.POST)
        noOfMembers = oMembers.count()
        
        oNotes = InitiativeNotes.objects.filter(initiative=oInitiative.id)
        noteForm = NoteForm(request.POST)
        #editNoteForm = NoteForm(instance=oNotes)
        noOfNotes = oNotes.count()
        
        oApprovalHistory = InitiativeApprovals.objects.filter(initiative=oInitiative.id)
        noOfApprovals = oApprovalHistory.count()

        if InitiativeFiles.objects.filter(initiative=oInitiative.id).first() != None:
            oInitiativeFiles = InitiativeFiles.objects.filter(initiative=oInitiative.id)
            initiativeFilesForm = FileForm(request.POST)
            noOfFiles = oInitiativeFiles.count()
        else:
            oInitiativeFiles = None
            initiativeFilesForm = FileForm(data=request.POST, files=request.FILES)
            noOfFiles = 0
        
        # selections = MTOScore.objects.filter(initiative=oInitiative)
        # cell_data = {s.cell_index: s.value for s in selections}
        saved_data ={}
        if oInitiative.unit:
            selections = MTOScore.objects.filter(
                initiative_id=oInitiative.id,
                unit_id=oInitiative.unit.id
            ).prefetch_related('values')
            
            saved_data = {
                sel.cell_index: [v.value for v in sel.values.all()]
                for sel in selections
            }
        
        #saved_data = {s.cell_index: s.value for s in selections.values.all()}
    
        return render(request, 'Fit4/Initiative/Init_Details.html', {
            'initiative':oInitiative, 'oPlanRelevance':oPlanRelevance, 
            'oEnabledBy':oEnabledBy, 'initiativeForm':initiativeForm, 
            'initiativeForm3':initiativeForm3, 'initiativeNextLGateForm':initiativeNextLGateForm, 
            'initiatives_formset':initiatives_formset, 'workstream':oWorkstream, 
            'form':benefitType, 'initiativeImpact':initiativeImpact, 
            'initiativeImpactForm':initiativeImpactForm, 'Zipformsets': Zipformsets, 
            'actions':oActions, 'actionsForm':actionsForm, 
            'noOfActions':noOfActions, 'members':oMembers, 
            'membersForm':membersForm, 'noOfMembers':noOfMembers, 
            'notes':oNotes, 'noteForm':noteForm,
            'noOfNotes':noOfNotes, 'oInitiativeFiles': oInitiativeFiles, 
            'initiativeFilesForm': initiativeFilesForm, 'noOfFiles': noOfFiles, 
            'allUsers':allUsers, 'oApprovalHistory':oApprovalHistory, 
            'noOfApprovals':noOfApprovals, 'initiativeThreatForm':initiativeThreatForm, 
            'assetHierarchyForm':assetHierarchyForm, 'oUnit':oUnit,
            'oProactiveType':oProactiveType, 'oThreatlikelihood':oThreatlikelihood, 
            'mtoScoringInfoForm':mtoScoringInfoForm, 'mtoScoringForm':mtoScoringForm, 
            'riskAssessmentForm':riskAssessmentForm, 'ZipUnits':ZipUnits, 
            'initiative_id': oInitiative.id, 'saved_data': json.dumps(saved_data), 
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return render(request, 'Fit4/Initiative/Init_Details.html', { 'error': 'An error occurred while loading the initiative details.'})


def check_file_view(request, url):
    # url = "https://example.com/path/to/file"  # Replace with actual file URL
    response = request.head(url)
    file_exists = response.status_code == 200

    return file_exists


#@login_required(login_url='account:login_page')
def change_owner(request, id):
    initiative = Initiative.objects.get(id=id)
    try:
        selected_user_id = request.POST.get('selected_user')
        if (request.user == initiative.author or request.user.is_staff or request.user.is_superuser):
            if request.method == "POST":
                initiative.author = User.objects.get(id=selected_user_id)
                initiative.save()
                # Send mail to the new user that the initiative has been reassigned to him/her
                ChangeInitiativeOwnerMail(request, initiative, selected_user_id) # commented out for now
                return redirect(reverse("Fit4:initiative_details", args=[initiative.slug]))
        else:
            messages.warning(request, "You have no right to change the user.")
            return redirect(reverse("Fit4:initiative_details", args=[initiative.slug]))
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[initiative.slug]))
    #return render(request, 'Fit4/Initiative_List.html', {'posts': initiative})

#endregion========================================= End Initiative ====================================================================================

#region================================================ Initiative Impact (Benefits) ==============================================================

#@login_required(login_url='account:login_page')
def add_benefits(request, id):
    try:
        if request.method == "POST":
            data = request.POST
            
            oInitiative = Initiative.objects.get(id=id)
            form = InitiativeImpactForm(request.POST)
            if form.is_valid():
                oBenefit = form.save(commit=False)
                oBenefit.initiative = oInitiative
                oBenefit.created_by = request.user
                oBenefit.save()
                # Update Currency in Initiative
                oInitiative.currency = Currency.objects.get(id = data.get('currency'))
                oInitiative.save()
                messages.success(request, "<b>Initiative Impact benefits sucessfully submitted.</b>")
                return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = InitiativeImpactForm()
    except Exception as e:
        print(traceback.format_exc())  
    return render(request, "partials/partial_add_benefits.html", {'initiativeImpact': form})

#@login_required(login_url='account:login_page')
def edit_benefits(request, id):
    try:
        oInitiativeImpact = InitiativeImpact.objects.get(id=id)
        oInitiative = Initiative.objects.get(id=oInitiativeImpact.initiative.id)
        
        if request.method == "POST":
            form = InitiativeImpactForm(data=request.POST, instance=oInitiativeImpact)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.last_modified_date = datetime.now()
                form.save()
                messages.success(request, "<b>Initiative Impact changes sucessfully updated.</b>")
            return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = InitiativeImpactForm(data=request.POST, instance=oInitiativeImpact)
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))


#@login_required(login_url='account:login_page')      
def delete_benefit(request, id):
    o = InitiativeImpact.objects.get(id=id)
    oInitiative = Initiative.objects.get(id=o.initiative.id)
    
    try:
        
        #if request.method == "POST":
            #if request.user == o.author:
        o.delete()
        messages.success(request, '<b>'+ o.title + '</b> successfully deleted.')
        return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        #else:
        #    messages.success(request, 'Deleted Not Successful.')
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
    
#endregion============================================ End Initiative Impact (Benefits) ============================================================

#region================================================ Actions ===================================================================================

#@login_required(login_url='account:login_page')
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

#@login_required(login_url='account:login_page')
def action_details(request, id):  
    oAction = Actions.objects.get(id=id)
    actionForm = ActionsForm(instance=oAction)
    return render(request, 'Fit4/Initiative/actions_details.html', {'form':oAction, 'actionsForm':actionForm})

#@login_required(login_url='account:login_page')
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

#@login_required(login_url='account:login_page')
def add_member(request, id):
    try:
        if request.method == "POST":
            form = MemberForm(request.POST)
            if form.is_valid():
                oMember = form.save(commit=False)
                oMember.initiative = Initiative.objects.get(id=id)
                oMember.created_by = request.user
                oMember.last_modified_by = request.user
                oMember.send_email = True
                oMember.save()
                return redirect('/en/member_details/'+ str(oMember.id))
                #return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
        else:
            form = ActionsForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "partials/partial_add_member.html", {'form': form})

#@login_required(login_url='account:login_page')
def member_details(request, id): 
    oMember = TeamMembers.objects.get(id=id)
    memberForm = MemberForm(instance=oMember)
    return render(request, 'Fit4/Initiative/member_details.html', {'form':oMember, 'memberForm':memberForm})

#@login_required(login_url='account:login_page')
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

#@login_required(login_url='account:login_page')
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

#@login_required(login_url='account:login_page')
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

#@login_required(login_url='account:login_page')
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

#region================================================ Approval Process ==========================================================================

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
    
class LGateIndex(Enum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    L6 = 6

#region ============================ Advance to Next L Gate refined ===========================

def validate_date_order1(request, o):
    stages = [
        ('L0_Completion_Date_Planned', 'L1_Completion_Date_Planned'),
        ('L1_Completion_Date_Planned', 'L2_Completion_Date_Planned'),
        ('L2_Completion_Date_Planned', 'L3_Completion_Date_Planned'),
        ('L3_Completion_Date_Planned', 'L4_Completion_Date_Planned'),
        ('L4_Completion_Date_Planned', 'L5_Completion_Date_Planned'),
    ]
    for earlier, later in stages:
        if getattr(o, earlier) > getattr(o, later):
            messages.warning(request, f'<b>Date error between {earlier} and {later}. Please review.</b>')
            return False
    return True

def assign_approvers(initiative, workstream):
    if not initiative.activate_initiative_approvers:
        initiative.workstreamlead = workstream.user_workstreamlead
        initiative.financesponsor = workstream.user_financesponsor
        initiative.workstreamsponsor = getattr(workstream, 'user_workstreamsponsor', None)

def advance_to_next_LGateNew(request, id):
    oInitiative = get_object_or_404(Initiative, id=id)
    oWorkstream = get_object_or_404(Workstream, id=oInitiative.Workstream.id)

    if request.method != "POST" or request.user != oInitiative.author:
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

    form = InitiativeNextLGateForm(data=request.POST, instance=oInitiative)
    if not form.is_valid():
        messages.error(request, 'Form validation failed.')
        return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

    o = form.save(commit=False)


    if any([oInitiative.workstreamsponsor, oInitiative.workstreamlead, oInitiative.financesponsor]) and not oInitiative.activate_initiative_approvers:
        messages.warning(request, '<b>Activate Initiative Approvers</b> must be clicked.')
        return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

    if not validate_date_order(request, o):
        return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

    try:
        assign_approvers(o, oWorkstream)
        gate_index = o.actual_Lgate.GateIndex

        # Close previous stage
        setattr(o, f'L{gate_index}_Completion_Date_Actual', now())
        o.Planned_Date = getattr(o, f'L{gate_index}_Completion_Date_Planned')
        o.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Pending.value)
        o.last_modified_by = request.user
        o.last_modified_date = now()

        # Update next gate
        if gate_index < LGateIndex.L5.value:
            o.actual_Lgate = Actual_L_Gate.objects.get(GateIndex=gate_index + 1)

        o.save()

        # Log approvals
        create_approval(oInitiative, gate_index + 1, "Approval Request Submitted", oInitiative.author)

        approver = (
            oInitiative.financesponsor if gate_index >= LGateIndex.L4.value
            else oInitiative.workstreamlead if oInitiative.activate_initiative_approvers
            else oWorkstream.user_workstreamlead
        )
        role = "Finance Sponsor" if gate_index >= LGateIndex.L4.value else "Workstream Lead"
        create_approval(oInitiative, gate_index + 1, role, approver)

        # Send mail based on stage
        if gate_index == LGateIndex.L1.value:
            InitiativeOwnerSendmailToWorkStreamLead(request, oInitiative)
        elif gate_index == LGateIndex.L4.value:
            WorkStreamLeadSendmailToFinanceSponsorCopyInitiativeOwner(request, oInitiative)
        elif gate_index == LGateIndex.L5.value:
            InitiativeOwnerSendmailToFinanceSponsor(request, oInitiative)

        messages.success(request, f'<b>Initiative successfully sent for L{gate_index + 1} approval.</b>')
        return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

    except Exception as e:
        print(traceback.format_exc())
        messages.error(request, 'An error occurred. Please contact admin.')
        return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

#endregion ===================================================================================


#region ======================= Advance to Next L Gate ========================================
def advance_to_next_LGate(request, id):
    try:
        oInitiative = Initiative.objects.get(id=id)
        oWorkstream = Workstream.objects.get(id=oInitiative.Workstream.id)
        if request.method == "POST" and request.user == oInitiative.author:
            form = InitiativeNextLGateForm(data=request.POST, instance=oInitiative)
            if form.is_valid():
                o = form.save(commit=False)
                
                if not validate_approvers_order(request, oInitiative):
                    messages.warning(request, '<b>Activate Initiative Approvers</b> must be clicked.')
                    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
                
                #validate_approvers_activated(request, oInitiative)
                if any([oInitiative.workstreamsponsor, oInitiative.workstreamlead, oInitiative.financesponsor]) and not oInitiative.activate_initiative_approvers:
                    messages.warning(request, '<b>Activate Initiative Approvers</b> must be clicked.')
                    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

                if not validate_date_order(request, o):
                    return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))
                
                #validate_initiative_impact(request, oInitiative)
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
    if initiative.activate_initiative_approvers:
        if initiative.workstreamsponsor == initiative.workstreamlead:
            messages.warning(request, '<b>Workstream Sponsor cannot be the same as Workstream Lead</b>')
        elif initiative.financesponsor == initiative.workstreamlead:
            messages.warning(request, '<b>Finance Sponsor cannot be the same as Workstream Lead</b>')
        elif initiative.financesponsor == initiative.workstreamsponsor:
            messages.warning(request, '<b>Finance Sponsor cannot be the same as Workstream Sponsor</b>')
        elif initiative.author in [initiative.workstreamsponsor, initiative.workstreamlead, initiative.financesponsor]:
            messages.warning(request, '<b>Initiative Owner cannot be same as any approver</b>')
        else:
            return True
        return False
    #return True

#TODO: kindly check this code. If no user is selected, it should not force user to select approvers
def validate_approvers_activated(request, oInitiative):
    #This is important when a user selects other users for approval other than the admin specific approvers in the system
    if(oInitiative.workstreamsponsor or oInitiative.workstreamlead or oInitiative.financesponsor):
        if (oInitiative.activate_initiative_approvers == False):
            messages.warning(request, '<b>Activate Initiative Approvers</b> must be clicked if you are selecting approvers other than the workstream specified approvers.')
            return redirect(reverse("Fit4:initiative_details", args=[oInitiative.slug]))

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
        messages.warning(request, '<b>Initiative Impact is required for L2 (Validate) Gate</b>')
        return redirect(reverse("Fit4:initiative_details", args=[initiative_slug]))
    return None

#=================== Workflow starts here ========================

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
    o.L0_Completion_Date_Actual = datetime.now() # Close Actual Completion Date for L0
    o.last_modified_by = request.user
    o.update = datetime.now()
    o.save()

    # Approval Request Submitted
    initiativeApprover = oInitiative.author
    submit_initiative_to_approver(oInitiative, LGateIndex.L1.value, "Approval Request Submitted", request.user, initiativeApprover)

def gateOne(request, o, oInitiative, oWorkstream):
    o.Planned_Date = o.L1_Completion_Date_Planned
    o.L1_Completion_Date_Actual = datetime.now() # Close Actual Completion Date for L1
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
    o.last_modified_date = datetime.now()
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
    o.last_modified_date = datetime.now()
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
    o.last_modified_date = datetime.now()
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
    o.last_modified_date = datetime.now()
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
    o.last_modified_date = datetime.now()
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

#=================== Workflow ends here ==========================


#endregion =================================================================================

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
        Created_Date=datetime.now()
    )

def update_initiative_gate(initiative, gate_index, visual_status_id, completion_date_field):
    setattr(initiative, 'actual_Lgate', Actual_L_Gate.objects.get(GateIndex=gate_index))
    initiative.approval_status_visual = approvalStatusVisual.objects.get(id=visual_status_id)
    setattr(initiative, completion_date_field, datetime.now())
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

#@login_required(login_url='account:login_page')
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

#@login_required(login_url='account:login_page')
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

#endregion============================================= Approval Process ==============================================================================

#region=============================================== FCF Multipliers ===========================================================================

#@login_required(login_url='account:login_page')
def FCF_Multiplier_list(request):
    fcfmultipliers = FCFMultiplier.objects.all().order_by('-Created_Date')
    form = FCFMultiplierForm(request.POST)
    return render(request, 'Fit4/FCF/index.html', {'fcfmultipliers': fcfmultipliers, 'form': form})

#@login_required(login_url='account:login')
def add_fcf_multiplier(request):
    try:
        if request.method == "POST":
            form = FCFMultiplierForm(request.POST)
            if form.is_valid():
                oMultiplier = form.save(commit=False)
                oMultiplier.save()
                return redirect('/en/calculator')
        else:
            form = FCFMultiplierForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/FCF/partial_fcfcalculator.html", {'form': form})

#@login_required(login_url='account:login_page')
def edit_fcf_multiplier(request, id):
    try:
        oFCFMultiplier = FCFMultiplier.objects.get(id=id)
        if request.method == "POST":
            form = FCFMultiplierForm(data=request.POST, instance=oFCFMultiplier)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()
                return redirect('/en/FCF_Calculator/'+ str(id))
        else:
            form = FCFMultiplierForm(instance=oFCFMultiplier)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/FCF/partial_fcfcalculator.html", {'form': form})

#@login_required(login_url='account:login_page')
def fcf_calculator_details(request, id):   
    oMultiplier = FCFMultiplier.objects.get(id=id)
    multiplierForm = FCFMultiplierForm(instance=oMultiplier)
    return render(request, 'Fit4/FCF/calculator_configuration.html', {'form':oMultiplier, 'multiplierForm':multiplierForm})

#endregion========================================================================================================================================

#region===================================MTO Scoring=============================================================================================

#@login_required(login_url='account:login_page')
def add_mtoscoring(request, initiativeId):
    try:
        if request.method == "POST":
            form = MTOScoringInfoForm(request.POST)
            if form.is_valid():
                oMultiplier = form.save(commit=False)
                oMultiplier.save()
                return redirect('/en/calculator')
        else:
            form = MTOScoringInfoForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/FCF/partial_fcfcalculator.html", {'form': form})



#endregion========================================================================================================================================

#region =========== Unit Management ==========================

def units(request):
    try:
        oUnit=Unit.objects.filter(active=True)
        unitForm = UnitForm(request.POST)
    except Exception:
        print(traceback.format_exc())
    return render(request, 'MTO/units.html', {'oUnit': oUnit, 'unitForm':unitForm})

def add_unit(request):
    try:
        if request.method == "POST":
            form = UnitForm(request.POST)
            if form.is_valid():
                o = form.save(commit=False)
                o.save()
                return redirect('/en/units')
        else:
            form = UnitForm()
    except Exception as e:
        print(traceback.format_exc())
    return redirect('/en/units')

@csrf_exempt
def edit_unit(request):
    try:
        if request.method == "POST":
            unit_id = request.POST.get("id")
            oUnit = Unit.objects.get(id=unit_id)
            oUnit.name = request.POST.get("name")
            oUnit.rated_capacity = request.POST.get("rated_capacity")
            oUnit.UOM = request.POST.get("UOM")
            oUnit.margin = request.POST.get("margin")
            oUnit.active = request.POST.get("active")
            oUnit.save()
            return redirect('/en/units')
    except Exception:
        print(traceback.format_exc())
    return redirect('/en/units')

#endregion==========================================================


#region =========== MTO Impact calculator ==========================

def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None

def impact_entry(request, oUnit, slug):
    initiative = get_object_or_404(Initiative, slug=slug)
    for o in oUnit:
        UnitImpactEntry.objects.create(unit=o, initiative=initiative, percent_impact=0, days=0)
    return None

def impact_entry_view(request, slug):
    try:
        PotentialProductionCost = 0
        initiative = get_object_or_404(Initiative, slug=slug)
        oUnit=Unit.objects.filter(Q(active=True) | Q(pk=initiative.unit.pk)).annotate(is_selected=Case(When(id=initiative.unit.pk, then=Value(0)), default=Value(1), output_field=IntegerField())).order_by('is_selected', 'name')  
        if request.method == 'POST':
            for o in oUnit:
                # Fetch the object
                #op = UnitImpactEntry.objects.get(unit=o, initiative=initiative)
                op = get_or_none(UnitImpactEntry, unit=o, initiative=initiative)
                # Update fields
                pt = request.POST.get('impact_percent_' + str(o.id))
                dt = request.POST.get('days_' + str(o.id))
                op.percent_impact=pt
                op.days=dt
                op.impact_day = float(pt) * float(o.rated_capacity or 0)
                op.financial_impact = float(pt) * float(o.rated_capacity or 0) * float(dt)
                PotentialProductionCost = PotentialProductionCost + (float(pt) * float(o.rated_capacity or 0) * float(dt))
                # Save changes to unitimpact model
                op.save()

                #Then update the fields (PotentialProductionCost and PotentialNonProductionCost) in initiative model
            initiative.PotentialProductionCost = PotentialProductionCost
            initiative.PotentialNonProductionCost = float(request.POST.get('PotentialNonProductionCost') or 0)
            initiative.calculated_asset_consequences = float(PotentialProductionCost) + float(request.POST.get('PotentialNonProductionCost') or 0)
            initiative.save()
    except Exception:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[slug]))

#endregion ==============================================

#region =================== MTO Scoring form ==================

def save_cell_selection(request, initiative_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cell_index = data.get('cellIndex')
            values = data.get('value')
            initiative = Initiative.objects.get(id=initiative_id)
            unit = Unit.objects.get(id=initiative.unit.id)

            # Save or update the value in the database
            cell_selection, created = MTOScore.objects.update_or_create(
                cell_index=cell_index,
                unit=unit,
                initiative=initiative,
                #defaults={'value': value}
            )
            
            # Remove old values and add new ones
            SelectionValue.objects.filter(MTOScore_selection=cell_selection).delete()
            for val in values:
                SelectionValue.objects.create(MTOScore_selection=cell_selection, value=val)

            return JsonResponse({'status': 'success', 'updated': not created})
        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    
def MTORiskAssessment(request, slug):
    try:
        oInitiative = Initiative.objects.get(slug=slug)
        
        asset_consequences=list(AssetConsequence.objects.all())
        people_consequences=list(PeopleConsequences.objects.all())
        environment_consequences=list(EnvironmentalConsequences.objects.all())
        community_consequences=list(CommunityConsequences.objects.all())
        threat_likelihoods = list(ThreatLikelihood.objects.all())  # Should be at least 5
        
        mtoscores = SelectionValue.objects.filter(
            MTOScore_selection__initiative=oInitiative, 
            MTOScore_selection__unit=oInitiative.unit
            ).select_related('MTOScore_selection').annotate(
                    cell_index=F('MTOScore_selection__cell_index'),
            )

        if request.method == "POST":
            form = MTORiskAssessmentForm(data=request.POST, instance=oInitiative)
            o = form.save(commit=False)
            if form.is_valid():
                o = form.save(commit=False)
                o.mto_score=MTOScoreCalculator(oInitiative)
                o.asset_consequences=AssetConsequenceCalculator(oInitiative)

                for m in mtoscores:
                    if 0 <= m.MTOScore_selection.cell_index < 30:
                        for j in range(0, 6):
                            if m.value == 'Asset':
                                o.asset_consequence=asset_consequences[j]
                            elif m.value == 'Environment':
                                o.environmental_consequence=environment_consequences[j]
                            elif m.value == 'People':
                                o.people_consequence=people_consequences[j]
                            elif m.value == 'Community':
                                o.community_consequence=community_consequences[j]
                                
                for m in mtoscores:
                    if 0 <= m.MTOScore_selection.cell_index < 30:
                        for j in range(0, 5):
                            if m.value == 'Environment':
                                o.likelihood_environment_consequence=threat_likelihoods[j]
                            elif m.value == 'People':
                                o.likelihood_people_consequence=threat_likelihoods[j]
                            elif m.value == 'Community':
                                o.likelihood_community_consequence=threat_likelihoods[j]
   
                # 'primary_ram_box', 
                # 'primary_ram_color', 
                # 'second_ram_box', 
                # 'second_ram_color', 
                
                # 'highest_impact_category', 
                # 'second_highest_impact_category',
                
                o.last_modified_by=request.user
                o.save()
                return redirect(reverse("Fit4:initiative_details", args=[slug]))
                #return redirect('/en/calculator')
            else:
                form = MTORiskAssessmentForm(data=request.POST, instance=oInitiative)
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[slug]))

def AssetConsequenceCalculator(oInitiative):
    mtoscores = MTOScore.objects.filter(initiative=oInitiative, unit=oInitiative.unit).prefetch_related('values')

    severity = list(Severity.objects.all())  # Should be at least 6
    threat_likelihoods = list(ThreatLikelihood.objects.all())  # Should be at least 5

    # Initialize results
    results = { 'Asset': {'Consequence': 0, 'Likelihood': 0}, }

    for o in mtoscores:
        # Calculate indexes
        consequence_index = o.cell_index // 5
        likelihood_index = o.cell_index % 5

        # Skip invalid indexes
        if consequence_index >= len(severity) or likelihood_index >= len(threat_likelihoods):
            continue

        # Assign values for each selected type
        for value in o.values.all():
            value_type = value.value
            if value_type in results:
                results[value_type]['Consequence'] = severity[consequence_index].factor
                results[value_type]['Likelihood'] = threat_likelihoods[likelihood_index].factor

    # Calculate total score
    score = sum(
        result['Consequence'] * result['Likelihood'] for result in results.values()
    )
    return score


def MTOScoreCalculator(oInitiative):
    mtoscores = MTOScore.objects.filter(initiative=oInitiative, unit=oInitiative.unit).prefetch_related('values')

    severity = list(Severity.objects.all())  # Should be at least 6
    threat_likelihoods = list(ThreatLikelihood.objects.all())  # Should be at least 5

    # Initialize results
    results = {
        'Asset': {'Consequence': 0, 'Likelihood': 0},
        'Environment': {'Consequence': 0, 'Likelihood': 0},
        'People': {'Consequence': 0, 'Likelihood': 0},
        'Community': {'Consequence': 0, 'Likelihood': 0}
    }

    for o in mtoscores:
        # Calculate indexes
        consequence_index = o.cell_index // 5
        likelihood_index = o.cell_index % 5

        # Skip invalid indexes
        if consequence_index >= len(severity) or likelihood_index >= len(threat_likelihoods):
            continue

        # Assign values for each selected type
        for value in o.values.all():
            value_type = value.value
            if value_type in results:
                results[value_type]['Consequence'] = severity[consequence_index].factor
                results[value_type]['Likelihood'] = threat_likelihoods[likelihood_index].factor

    # Calculate total score
    score = sum(
        result['Consequence'] * result['Likelihood'] for result in results.values()
    )
    return score

#<!-- Keep this code as it is original one written, in case AI code fails -->
def MTOScoreCalculatorOption(oInitiative):
    mtoscores = MTOScore.objects.filter(initiative=oInitiative, unit=oInitiative.unit).prefetch_related('values')

    # Preload all required Severity and Likelihoods data
    severity = list(Severity.objects.all())  # Needs at least 6
    threat_likelihoods = list(ThreatLikelihood.objects.all())  # Needs at least 5
    
    # Initialize result holders
    Asset_Consequence = Asset_Likelihood = People_Consequence = People_Likelihood = Environmental_Consequence = Environmental_Likelihood = Community_Consequence = Community_Likelihood = 0
    
    for o in mtoscores:
        if 0 <= o.cell_index < 5:
            for j in range(0, 5):
                if o.value == 'Asset':
                    Asset_Consequence=severity[0].factor
                    Asset_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Environment':
                    Environmental_Consequence=severity[0].factor
                    Environmental_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'People':
                    People_Consequence=severity[0].factor
                    People_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Community':
                    Community_Consequence=severity[0].factor
                    Community_Likelihood=threat_likelihoods[j].factor
                    
        if 5 <= o.cell_index < 10:
            for j in range(0, 5):
                if o.value == 'Asset':
                    Asset_Consequence=severity[1].factor
                    Asset_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Environment':
                    Environmental_Consequence=severity[1].factor
                    Environmental_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'People':
                    People_Consequence=severity[1].factor
                    People_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Community':
                    Community_Consequence=severity[1].factor
                    Community_Likelihood=threat_likelihoods[j].factor
        
        if 10 <= o.cell_index < 15:
            for j in range(0, 5):
                if o.value == 'Asset':
                    Asset_Consequence=severity[2].factor
                    Asset_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Environment':
                    Environmental_Consequence=severity[2].factor
                    Environmental_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'People':
                    People_Consequence=severity[2].factor
                    People_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Community':
                    Community_Likelihood=threat_likelihoods[j].factor
                    Community_Consequence=severity[2].factor
       
        if 15 <= o.cell_index < 20:
            for j in range(0, 5):
                if o.value == 'Asset':
                    Asset_Consequence=severity[3].factor
                    Asset_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Environment':
                    Environmental_Consequence=severity[3].factor
                    Environmental_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'People':
                    People_Consequence=severity[3].factor
                    People_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Community':
                    Community_Consequence=severity[3].factor
                    Community_Likelihood=threat_likelihoods[j].factor     
        
        if 20 <= o.cell_index < 25:
            for j in range(0, 5):
                if o.value == 'Asset':
                    Asset_Consequence=severity[4].factor
                    Asset_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Environment':
                    Environmental_Consequence=severity[4].factor
                    Environmental_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'People':
                    People_Consequence=severity[4].factor
                    People_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Community':
                    Community_Consequence=severity[4].factor
                    Community_Likelihood=threat_likelihoods[j].factor     
       
        if 25 <= o.cell_index < 30:
            for j in range(0, 5):
                if o.value == 'Asset':
                    Asset_Consequence=severity[5].factor
                    Asset_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Environment':
                    Environmental_Consequence=severity[5].factor
                    Environmental_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'People':
                    People_Consequence=severity[5].factor
                    People_Likelihood=threat_likelihoods[j].factor
                elif o.value == 'Community':
                    Community_Consequence=severity[5].factor
                    Community_Likelihood=threat_likelihoods[j].factor
                            
    score = ((Asset_Consequence * Asset_Likelihood) + (People_Consequence * People_Likelihood) + (Environmental_Consequence * Environmental_Likelihood) + (Community_Consequence * Community_Likelihood))    
    return score


def ConsequenceLikelihood(oInitiative):
    mtoscores = MTOScore.objects.filter(initiative=oInitiative, unit=oInitiative.unit)

    # Preload consequences
    consequence_map = {
        'Asset': list(AssetConsequence.objects.all()),
        'People': list(PeopleConsequences.objects.all()),
        'Environment': list(EnvironmentalConsequences.objects.all()),
        'Community': list(CommunityConsequences.objects.all())
    }
    threat_likelihoods = list(ThreatLikelihood.objects.all())  # Shared for all types

    results = {
        'Asset': [],
        'People': [],
        'Environment': [],
        'Community': []
    }

    for o in mtoscores:
        if 0 <= o.cell_index < 30:
            consequence_index = o.cell_index // 5
            likelihood_index = o.cell_index % 5

            for c_type, c_list in consequence_map.items():
                try:
                    consequence = c_list[consequence_index]
                    likelihood = threat_likelihoods[likelihood_index]
                    results[c_type].append({'cell_index': o.cell_index, 'consequence': consequence, 'likelihood': likelihood, })
                except IndexError:
                    continue  # Ignore if index is out of range

    return results  # Dictionary of consequence types => list of dicts

#region def ConsequenceLikelihood(consequence_type, oInitiative):
#     mtoscores = MTOScore.objects.filter(initiative=oInitiative, unit=oInitiative.unit)
    
#     # Preload data
#     people_consequences = PeopleConsequences.objects.all()  # Needs at least 6
#     environment_consequences = EnvironmentalConsequences.objects.all()  # Needs at least 6
#     community_consequences = list(CommunityConsequences.objects.all())  # Needs at least 6
#     asset_consequences = list(AssetConsequence.objects.all())  # Needs at least 6
#     threat_likelihoods = list(ThreatLikelihood.objects.all())  # Needs at least 5
    
#     results = []

#     for o in mtoscores:
#         if consequence_type == 'Asset':
#             if 0 <= o.cell_index < 30:
#                 consequence_index = o.cell_index // 5  # 0 to 5
#                 likelihood_index = o.cell_index % 5    # 0 to 4

#                 consequence = asset_consequences[consequence_index]
#                 likelihood = threat_likelihoods[likelihood_index]

#                 results.append({'cell_index': o.cell_index, 'consequence': consequence, 'likelihood': likelihood,})
#         elif consequence_type == 'People':
#             if 0 <= o.cell_index < 30:
#                 consequence_index = o.cell_index // 5  # 0 to 5
#                 likelihood_index = o.cell_index % 5    # 0 to 4

#                 consequence = people_consequences[consequence_index]
#                 likelihood = threat_likelihoods[likelihood_index]

#                 results.append({'cell_index': o.cell_index, 'consequence': consequence, 'likelihood': likelihood,})
#         elif consequence_type == 'Enviroment':
#             if 0 <= o.cell_index < 30:
#                 consequence_index = o.cell_index // 5  # 0 to 5
#                 likelihood_index = o.cell_index % 5    # 0 to 4

#                 consequence = environment_consequences[consequence_index]
#                 likelihood = threat_likelihoods[likelihood_index]

#                 results.append({'cell_index': o.cell_index, 'consequence': consequence, 'likelihood': likelihood,})
#         elif consequence_type == 'Community':
#             if 0 <= o.cell_index < 30:
#                 consequence_index = o.cell_index // 5  # 0 to 5
#                 likelihood_index = o.cell_index % 5    # 0 to 4

#                 consequence = community_consequences[consequence_index]
#                 likelihood = threat_likelihoods[likelihood_index]

#                 results.append({'cell_index': o.cell_index, 'consequence': consequence, 'likelihood': likelihood,})
                
#     return results  # list of dicts

#def calculateMTOScore(oInitiative):
#     mtoscores = MTOScore.objects.filter(initiative=oInitiative, unit=oInitiative.unit).prefetch_related('values')
    
#     # Preload database values only once
#     asset_consequences = list(AssetConsequence.objects.all())  # Expecting at least 6 items
#     threat_likelihoods = list(ThreatLikelihood.objects.all())  # Expecting at least 5 items

#     # Initialize result holders
#     results = {
#         'Asset': {'Consequence': None, 'Likelihood': None},
#         'Community': {'Consequence': None, 'Likelihood': None},
#         'Environment': {'Consequence': None, 'Likelihood': None},
#         'People': {'Consequence': None, 'Likelihood': None}
#     }

#     for o in mtoscores:
#         if 0 <= o.cell_index < 30 and o.values.all() in results:
#             consequence_index = o.cell_index // 5
#             likelihood_index = o.cell_index % 5

#             # Assign values
#             results[o.value]['Consequence'] = asset_consequences[consequence_index]
#             results[o.value]['Likelihood'] = threat_likelihoods[likelihood_index]
            
#     return (
#         results['People']['Consequence'] * results['People']['Likelihood'] +
#         results['Environment']['Consequence'] * results['Environment']['Likelihood'] +
#         results['Community']['Consequence'] * results['Community']['Likelihood'] +
#         results['Asset']['Consequence'] * results['Asset']['Likelihood']
#           )


# def MTOScoreCalculator(oInitiative):
#     mtoscores = MTOScore.objects.filter(
#         initiative=oInitiative, unit=oInitiative.unit
#     ).prefetch_related('values')

#     # Preload all required consequence data
#     consequence_map = {
#         'Asset': list(AssetConsequence.objects.all()),
#         'People': list(PeopleConsequences.objects.all()),
#         'Environment': list(EnvironmentalConsequences.objects.all()),
#         'Community': list(CommunityConsequences.objects.all()),
#     }
#     threat_likelihoods = list(ThreatLikelihood.objects.all())

#     # Check all lists are sufficiently populated
#     for key, con_list in consequence_map.items():
#         if len(con_list) < 6:
#             raise ValueError(f"Expected at least 6 {key} consequences.")
#     if len(threat_likelihoods) < 5:
#         raise ValueError("Expected at least 5 ThreatLikelihood entries.")

#     # Initialize results
#     results = {k: {'Consequence': None, 'Likelihood': None} for k in consequence_map}

#     for o in mtoscores:
#         consequence_index = o.cell_index // 5  # 0–5
#         likelihood_index = o.cell_index % 5    # 0–4

#         for selection in o.values.all():
#             value_type = selection.value
#             if value_type in results:
#                 consequence_list = consequence_map[value_type]
#                 results[value_type]['Consequence'] = consequence_list[consequence_index]
#                 results[value_type]['Likelihood'] = threat_likelihoods[likelihood_index]

#     def get_score(key):
#         c = results[key]['Consequence']
#         l = results[key]['Likelihood']
#         return (getattr(c, 'factor', 0) or 0) * (getattr(l, 'factor', 0) or 0)

#     final_score = sum(get_score(k) for k in results)
#     return final_score

# def MTOScoreCalculator(oInitiative):
#     mtoscores = MTOScore.objects.filter(initiative=oInitiative, unit=oInitiative.unit).prefetch_related('values')

#     # Preload data
#     asset_consequences = list(AssetConsequence.objects.all())  # Needs at least 6
#     threat_likelihoods = list(ThreatLikelihood.objects.all())  # Needs at least 5

#     # Initialize result holders
#     results = {
#         'Asset': {'Consequence': None, 'Likelihood': None},
#         'Community': {'Consequence': None, 'Likelihood': None},
#         'Environment': {'Consequence': None, 'Likelihood': None},
#         'People': {'Consequence': None, 'Likelihood': None}
#     }

#     for o in mtoscores:
#         consequence_index = o.cell_index // 5
#         likelihood_index = o.cell_index % 5

#         # Ensure indexes are within bounds
#         if consequence_index >= len(asset_consequences) or likelihood_index >= len(threat_likelihoods):
#             continue

#         for selection in o.values.all():
#             value_type = selection.value
#             if value_type in results:
#                 results[value_type]['Consequence'] = asset_consequences[consequence_index]
#                 results[value_type]['Likelihood'] = threat_likelihoods[likelihood_index]

#     # Safely compute final score using .score (or change to actual numeric field)
#     def get_score(key):
#         c = results[key]['Consequence']
#         l = results[key]['Likelihood']
#         return (c.factor if c else 0) * (l.factor if l else 0)

#     scores = (get_score('People') + get_score('Environment') + get_score('Community') + get_score('Asset'))
#     return scores
#endregion
        
#endregion ===================================================