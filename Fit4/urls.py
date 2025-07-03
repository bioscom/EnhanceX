from django.urls import path
from . import views
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns

app_name = 'Fit4'

urlpatterns = [
    
    #   Administrative Areas
    path(_('admin'), admin.site.urls),

    #   Search
    path(_('search/'), views.search, name="search"), 
    
    #path(_(''), views.Home, name="home"), 
    
    #   Landing Home Page after logon
    path(_('home'), views.Home, name="home"),  #===>> Individuals View list of own initiatives, Actions and Initiatives pending approval
    
    path(_('recycleBin'), views.recycleBin, name="recycleBin"),
    
    #   Workstream,   Codes dealing with creaing Workstreams and maintenance
    path(_('workstream'), views.workstream_List, name="workstream_List"),
    path(_('add_workstream'), views.add_workstream, name="add_workstream"),
    path(_('wsdetails/<str:slug>'), views.workstream_details, name="workstream_details"),
    path(_('edit_workstream/<str:slug>'), views.edit_workstream, name="edit_workstream"),
    path(_('delworkstream/<int:id>/'), views.delete_workstream, name='delete_workstream'),
    path(_('assethierarchy/<str:slug>/'), views.update_workstream_assethierarchy, name="update_workstream_assethierarchy"),
    #d
    
    
    # Initiatives
    path("all/", views.initiatives_list, name="initiatives_list"),
    path("owners/<int:id>", views.initiatives_list, name="all_initiatives_list"),  #Owner's Initiatives
    path(_('add_initiative/'), views.add_initiative, name="add_initiative"),

    path(_('clone_initiative'), views.clone_initiative, name="clone_initiative"),
    path(_('clone_MTO_initiative'), views.clone_MTO_initiative, name="clone_MTO_initiative"),
    
    path(_('add_threat/'), views.add_threat, name="add_threat"),
    
    path(_('edit_initiative/<str:slug>/'), views.edit_initiative, name="edit_initiative"),
    path(_('update_assethierarchy/<str:slug>/'), views.update_AssetHierarchy, name="update_assethierarchy"),
    path(_('recall_initiative/<str:slug>/'), views.recall_initiative, name="recall_initiative"),

    #actions
    path(_('actions'), views.actions_list, name="actions_list"),

    #Pending
    path(_('pending'), views.pending_approval, name="pending_approval"),
    
    #update_workstream_assethierarchy
    path(_('edit_DocsLinks/<int:id>/'), views.edit_DocsLinks, name="edit_DocsLinks"),
    path(_('initiative/<str:slug>'), views.initiative_details, name="initiative_details"),
    path(_('delete/<int:id>/'), views.delete_initiative, name='delete_initiative'),
    
    path(_('change_owner/<int:id>/'), views.change_owner, name='change_owner'),
    path(_('advance/<int:id>/'), views.advance_to_next_LGate, name='advance_to_next_LGate'),
    path(_('addfile/<int:id>/'), views.add_file, name='add_file'),
    path(_('check_file_view/<str:url>/'), views.check_file_view, name='check_file_view'),
    path(_('addNote/<int:id>/'), views.add_note, name='add_note'),
    path(_('edit_note/<int:id>/'), views.edit_note, name='edit_note'),
    
    path(_('approval_details/<int:id>/'), views.approval_details, name='approval_details'),
    path(_('approve_initiative/<int:id>/'), views.approve_initiative, name='approve_initiative'),
    path(_('reject_initiative/<int:id>/'), views.reject_initiative, name='reject_initiative'),
    path(_('reassign_initiative/<int:id>/'), views.reassign_initiative, name='reassign_initiative'),
    
    # Initiative Impact
    path(_('add_benefits/<int:id>'), views.add_benefits, name="add_benefits"),
    path(_('edit_benefits/<int:id>'), views.edit_benefits, name="edit_benefits"),
    path(_('delete_benefit/<int:id>'), views.delete_benefit, name="delete_benefit"),
    
    # Actions
    path(_('add_actions/<int:id>'), views.add_actions, name="add_actions"),
    path(_('actions_details/<int:id>'), views.action_details, name="action_details"),
    path(_('edit_actions/<int:id>'), views.edit_actions, name="edit_actions"),
    #path(_('my_actions/<int:id>'), views.my_actions, name="my_actions"),
    
    # Members
    path(_('add_member/<int:id>'), views.add_member, name="add_member"),
    path(_('member_details/<int:id>'), views.member_details, name="member_details"),
    path(_('edit_member/<int:id>'), views.edit_member, name="edit_member"),
    
    # Actual Lgate Predefined Approvers
    #
    # path(_('create/'), views.create_predefinedApproversLgate, name="create_predefinedApproversLgate"),
    path(_('approvers/<int:id>/view'), views.update_predefinedApprovers, name="update_predefinedApprovers"),

    # FCF Calculator
    path("calculator", views.FCF_Multiplier_list, name="FCF_Multiplier_list"),
    path("multiplier", views.add_fcf_multiplier, name="add_fcf_multiplier"),
    path("FCF_Calculator/<int:id>", views.fcf_calculator_details, name="fcf_calculator_details"),
    path("edit_FCF_Calculator/<int:id>", views.edit_fcf_multiplier, name="edit_fcf_multiplier"),
    
    # Banner Management
    path("banners/", views.banner_list, name="banner_list"),
    path("add_banner/", views.add_banner, name="add_banner"),
    path("update_banner/<int:id>", views.update_banner, name="update_banner"),
    path("delete_banner/<int:id>", views.delete_banner, name="delete_banner"),
    
    # units 
    path("units", views.units, name="units"),
    path("add_unit", views.add_unit, name="add_unit"),
    path("edit_unit", views.edit_unit, name="edit_unit"),
    
    
    path("risk_assessment/<str:slug>", views.MTORiskAssessment, name="risk_assessment"),
    path('impact/<str:slug>', views.impact_entry_view, name='impact_entry'),
    path('save-cell-selection/<int:initiative_id>/', views.save_cell_selection, name='save_cell_selection'),
    
]