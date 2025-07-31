from .models import Initiative
from Fit4.forms import *
from reports.models import *
from dashboard.utilities import *

def global_function(request):
    Top5Initiatives = []
    if request.user.is_authenticated:
        Top5Initiatives = Initiative.objects.filter(author=request.user).order_by('-Created_Date').order_by("?") [:10]
    oReports = SavedFilter.objects.all()
    return {'Top5':Top5Initiatives, 'oReport':oReports}


def global_Initiative(request):
    form = InitiativeForm(request.POST)
    threatForm = InitiativeThreatForm(request.POST)

    return {'form': form, 'threatForm':threatForm, }

def global_initiative_data(request):
    return get_weekly_initiative_reports()


def global_forms(request):
    return {
        'initiativeForm': InitiativeForm(),         # Or any default initialization you want
        'threatForm': InitiativeThreatForm()
    }
    
    #form = InitiativeForm(request.POST)
    #threatForm = InitiativeThreatForm(request.POST)