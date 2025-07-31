from django.urls import path
from . import views, view_opex_report, view_delivery_report, views_dashboard_plotly_graphs, views_mto_dashboard
from django.utils.translation import gettext_lazy as _

app_name = 'dashboard'

urlpatterns = [
    path('dashboard', views.home_dashboard, name='home_dashboard'),
    path(_('newDashboard'), views.add_dashboard, name='add_dashboard'),
    path(_('edit/<int:id>'), views.edit_dashboard, name='edit_dashboard'),
    #path(_('dashboard/<str:dashboard_id>/view'), views.chart, name='dashboard_view'),
    path(_('dashboard/<str:dashboard_id>/view'), views.dashboard_view, name='dashboard_view'),
    path(_("dashboards/<str:dashboard_id>/view"), views.dashboard_view2, name="dashboards"),
    path(_("dashboards/<int:id>"), views.delete_dashboard, name="delete_dashboard"),
    
    #delete_dashboard
    
    path(_("dashboards_mto"), views.dashboard_MTO, name="dashboards_mto"),
    path(_("opex_report"), views.opex_report, name="opex_report"),
    path(_("delivery_report"), views.delivery_report, name="delivery_report"),
    #path(_("capex_report"), views.capex_report, name="capex_report"),
    #path(_("commercial_report"), views.commercial_report, name="commercial_report"),

    path(_("sync-data/"), views.trigger_opex_data_copy, name="trigger_opex_data_copy"),
    path(_("add_opex_recognition"), views.add_opex_recognition, name="add_opex_recognition"),
    path(_("edit_opex_recognition"), views.edit_opex_recognition, name="edit_opex_recognition"),
    path('opex/ajax/load-week-data/', views.ajax_show_opex_last_week, name='ajax_show_delivery_last_week'),

    path(_("sync-delivery-data/"), views.trigger_delivery_data_copy, name="trigger_delivery_data_copy"),
    path(_("add_delivery_recognition"), views.add_delivery_recognition, name="add_delivery_recognition"),
    path(_("edit_delivery_recognition"), views.edit_delivery_recognition, name="edit_delivery_recognition"),
    
    path(_("add-delivery-target"), view_delivery_report.add_delivery_target, name="add_delivery_target"),
    path(_("edit-delivery-target"), view_delivery_report.edit_delivery_target, name="edit_delivery_target"),
    path(_("delivery/delete/<int:id>"), views.delete_delivery_duplicate, name='delete_delivery_duplicate'),
    path(_("opex/delete/<int:id>"), views.delete_opex_duplicate, name='delete_opex_duplicate'),

    path(_("add-opex-target"), view_opex_report.add_opex_target, name="add_opex_target"),
    path(_("edit-opex-target"), view_opex_report.edit_opex_target, name="edit_opex_target"),
    #
    path('upload-excel/', views.upload_weekly_commitment_excel, name='upload_excel'),
    
    
]