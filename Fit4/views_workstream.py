from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import Initiative, Workstream
from django.contrib.auth.decorators import login_required
from Fit4.forms import *
from django.contrib import messages
from django.contrib.auth.models import User
import traceback
from user_visit.models import *
from django.utils.timezone import now


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


def workstream_List(request):
    oWorkStream = Workstream.objects.all()
    workStreamForm = WorkStreamForm(request.POST)
    return render(request, 'Fit4/Workstream/workstream_list.html', {'workstreams': oWorkStream, 'workstreamform':workStreamForm})

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

def delete_workstream(request, id):
    o = Workstream.objects.get(id=id)
    if request.method == "POST":
        if request.user == o.author:
            #TODO: Kindly put this on suspension, as deleting a workstream could delete an entire initiatives in the workstream. Delete a workstream should archive it.
            #o.delete()
            messages.success(request, '<b>'+ o.workstreamname + '</b> successfully deleted.')
            return redirect('/en/workstream')
    return render(request, 'Fit4/Initiative_List.html', {'posts': o})


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