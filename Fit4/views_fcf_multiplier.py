from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from Fit4.forms import *
import traceback
from user_visit.models import *



def FCF_Multiplier_list(request):
    fcfmultipliers = FCFMultiplier.objects.all().order_by('-Created_Date')
    form = FCFMultiplierForm(request.POST)
    return render(request, 'Fit4/FCF/index.html', {'fcfmultipliers': fcfmultipliers, 'form': form})


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


def fcf_calculator_details(request, id):   
    oMultiplier = FCFMultiplier.objects.get(id=id)
    multiplierForm = FCFMultiplierForm(instance=oMultiplier)
    return render(request, 'Fit4/FCF/calculator_configuration.html', {'form':oMultiplier, 'multiplierForm':multiplierForm})

#endregion========================================================================================================================================




