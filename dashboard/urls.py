from django.urls import path
from . import views
from django.utils.translation import gettext_lazy as _

app_name = 'dashboard'

urlpatterns = [
    path('dashboard', views.home_dashboard, name='home_dashboard'),
    path(_('newDashboard'), views.add_dashboard, name='add_dashboard'),
    path(_('edit/<int:id>'), views.edit_dashboard, name='edit_dashboard'),
    #path(_('dashboard/<str:dashboard_id>/view'), views.chart, name='dashboard_view'),
    path(_('dashboard/<str:dashboard_id>/view'), views.dashboard_view, name='dashboard_view'),
    path(_("dashboards/<str:dashboard_id>/view"), views.dashboard_view2, name="dashboards"),
    
    path(_("dashboards_mto"), views.dashboard_MTO, name="dashboards_mto"),
    
    path(_("management_report"), views.management_report, name="management_report"),
    path(_("sync-data/"), views.trigger_opex_data_copy, name="trigger_opex_data_copy"),
    path(_("add_opex_recognition"), views.add_opex_recognition, name="add_opex_recognition"),
    
    path(_("sync-delivery-data/"), views.trigger_delivery_data_copy, name="trigger_delivery_data_copy"),
    path(_("add_delivery_recognition"), views.add_opex_recognition, name="add_delivery_recognition"),
    
]