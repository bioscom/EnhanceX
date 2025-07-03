import json
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.http import HttpResponseBadRequest
from .models import Initiative, Workstream
from django.contrib.auth.decorators import login_required
from Fit4.forms import *
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count, Case, When, Value, IntegerField
import traceback
from django.contrib.auth import get_user_model
from user_visit.models import *
import datetime
from datetime import datetime
from django.urls import reverse
from .notifications import *
from itertools import zip_longest
from django.db.models import Q, F, Prefetch
from enum import Enum

from .views_mto import *

#region =============================================== Initiatives ==============================================================================

def add_initiative(request):
    try:
        if request.method == "POST":
            form = InitiativeForm(request.POST)
            if form.is_valid():
                oInitiative = form.save(commit=False)
                oInitiative.author = request.user
                oInitiative.initiative_id = ControlSequence.get_next_number('R') #"R-" + create_object()
                oInitiative.YYear = datetime.datetime.now().year
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
                o.YYear = datetime.datetime.now().year
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

def add_threat(request):
    try:
        if request.method == "POST":
            form = InitiativeThreatForm(request.POST)
            if form.is_valid():
                oInitiative = form.save(commit=False)
                oInitiative.author = request.user
                oInitiative.initiative_id = ControlSequence.get_next_number('R') #"R-" + create_object()
                oInitiative.YYear = datetime.datetime.now().year
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

def clone_MTO_initiative(request):
    try:
        if request.method == "POST":
            form = InitiativeThreatForm(request.POST)
            if form.is_valid():
                oInitiative = form.save(commit=False)
                oInitiative.author = request.user
                oInitiative.initiative_id = ControlSequence.get_next_number('R') #"R-" + create_object()
                oInitiative.YYear = datetime.datetime.now().year
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
        
    return render(request, "partials/partial_clone_threat.html", {'form': form})

def update_AssetHierarchy(request, slug):
    try:
        oInitiative = Initiative.objects.get(slug=slug)
        oWorkstream = Workstream.objects.get(id=oInitiative.Workstream.pk)
        if request.method == "POST":
            form = AssetHierarchyForm(data=request.POST, instance=oInitiative)
            if form.is_valid():
                o = form.save(commit=False)
                #oInitiative.currency = Currency.objects.get(title='US Dollar')
                #oInitiative.YYear = datetime.datetime.now().year
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
                o.YYear = datetime.datetime.now().year
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

        current_year = datetime.datetime.now().year
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

def change_owner(request, id):
    initiative = None
    try:
        initiative = Initiative.objects.get(id=id)
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
    if initiative is not None:
        return redirect(reverse("Fit4:initiative_details", args=[initiative.slug]))
    else:
        return redirect('/en/home')
    #return render(request, 'Fit4/Initiative_List.html', {'posts': initiative})

def recall_initiative(request, slug):
    try:
        initiative = Initiative.objects.get(slug=slug)
        if request.method == "POST":
            approval = InitiativeApprovals.objects.filter(Q(initiative=initiative), Q(status__isnull=True))
            approval.update(status=ApprovalStatus.Recalled.value)
            
            initiative.approval_status_visual = approvalStatusVisual.objects.get(id=ApprovalVisualStatus.Recalled.value)
            initiative.save()

            messages.success(request, "<b>Initiative has been recalled successfully.</b>")
            return redirect(reverse("Fit4:initiative_details", args=[initiative.slug]))
    except Exception as e:
        print(traceback.format_exc())
    return redirect(reverse("Fit4:initiative_details", args=[initiative.slug]))

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
                o.last_modified_date = datetime.datetime.now()
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