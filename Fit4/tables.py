from .models import *
from table import Table
from table.columns import Column

class InitiativeTable(Table):
    id = Column(field='id')
    initiative_name = Column(field='initiative_name')
    class Meta:
        model = Initiative