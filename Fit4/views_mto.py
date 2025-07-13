import json
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from Fit4.forms import *
from django.db.models import Q, Count, Case, When, Value, IntegerField
import traceback
from user_visit.models import *
from django.http import JsonResponse
from django.urls import reverse
from .notifications import *
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, Prefetch
from django.utils.timezone import now

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