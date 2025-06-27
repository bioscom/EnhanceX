from django.urls import path

from reports import views
from django.utils.translation import gettext_lazy as _

app_name='reports'

urlpatterns = [
    path(_('report/cat'), views.category_list, name='catetogy_list'),
    path(_('report/editCat/<int:id>'), views.edit_category, name='edit_category'),
    #path(_('newReport'), views.add_report, name='add_report'),
    path(_('SaveAs/<str:filter_id>'), views.save_as, name='save_as'),
    


    #Report Home page
    path(_('rhome'), views.home_report, name='home_report'),
    path(_('created-by-me'), views.created_by_me_report, name='created_by_me'),
    path(_('created-by-others'), views.created_by_others, name='created_by_others'),
    #created_by_others
    path(_('filters/<int:category_id>/create'), views.report_filter, name="report_filter"),    # This is where a report is created
    path(_('filters/<int:category_id>'), views.save_filter, name="save_filter"),
    path(_('filters/<str:filter_id>/edit'), views.edit_filter, name="edit_filter"),
    path(_('<str:report_id>/view'), views.report_view, name='report_view'),
    path(_('delete/<int:id>'), views.delete_filter, name='delete_filter'),
    path(_('addtoDashboard/<str:filter_id>'), views.add_savedfilter_todashboard, name='add_savedfilter_todashboard'),
    
    path('fetch-metadata/', views.fetch_metadata, name='fetch_metadata'),

    
    #path(_('filters/<str:filter_id>/edit'), views.update_report, name='update_report'),

    #path('sales-report/<str:report_id>/', views.sales_report_view, name='sales_report'),
    #path('sales-report-page/<str:report_id>/', views.sales_report_page, name='sales_report_page'),
    # path('d/<str:report_id>/', views.ReportsDetailView.as_view(), name='report_detail'),

    # #
    # 
    # path(_('report/'), views.get_report_header, name='report'),
    # path(_('report/<str:report_id>/edit'), views.report_edit, name='report_edit'),
    # path(_('export/<int:id>/'), views.export_to_excel, name='export_to_excel'),
]
