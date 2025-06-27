from .models import Initiative
from Fit4.forms import *
from reports.models import *

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