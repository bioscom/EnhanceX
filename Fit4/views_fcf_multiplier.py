from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from Fit4.forms import *
import traceback
from user_visit.models import *
from django.utils.timezone import now
from django.http import JsonResponse


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
                oMultiplier.last_modified_by = request.user
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


def FCF_calculator_list(request):
    assets = Asset.objects.all().order_by('id')
    savings = Savings.objects.all().order_by('id')
    production_fcf = ProductionFCF.objects.all().order_by('id')
    form = AssetForm(request.POST)
    savingsForm = SavingsForm(request.POST)
    productionFCFForm = ProductionFCFForm(request.POST)
    return render(request, 'Fit4/FCF/fcf_calc.html', {'assets': assets, 'savings': savings, 'production_fcf': production_fcf, 'form': form})

def add_fcf_calculator(request):
    try:
        if request.method == "POST":
            form = AssetForm(request.POST)
            if form.is_valid():
                oCalculator = form.save(commit=False)
                oCalculator.last_modified_by = request.user
                oCalculator.save()
                return redirect(reverse("Fit4:cat_list"))
        else:
            form = AssetForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/FCF/partial_add_fcf_calculator.html", {'form': form})

def edit_fcf_calculator(request, id):
    try:
        oFCFCalculator = Asset.objects.get(id=id)
        if request.method == "POST":
            form = AssetForm(data=request.POST, instance=oFCFCalculator)
            if form.is_valid():
                o = form.save(commit=False)
                o.last_modified_by = request.user
                o.save()
                return redirect(reverse("Fit4:cat_list"))
        else:
            form = AssetForm(instance=oFCFCalculator)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/FCF/partial_add_fcf_calculator.html", {'form': form})

def get_asset_factors(request):
    asset_name = request.GET.get('asset', '').strip()
    try:
        asset = Asset.objects.get(asset=asset_name)
        return JsonResponse({
            'capex_factor': asset.capex_factor,
            'opex_factor': asset.opex_factor,
            'oil_factor': asset.oil_factor,
            'domgas_factor': asset.domgas_factor,
            'export_gas_factor': asset.export_gas_factor,
            'renaissance_share': asset.renaissance_share,
        })
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found'}, status=404)

#endregion========================================================================================================================================




