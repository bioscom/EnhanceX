from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from django.utils.translation import gettext_lazy as _
from .views import UserPasswordChangeView

app_name = 'account'

urlpatterns = [
    # previous login view
    path('', views.user_login2, name='login_page'),   # This is the entry point for the application
    path(_('login_page'), views.user_login2, name='login_page'),
    path(_('login_as/<str:username>'), views.login_as, name='login_as'),
    path('logout/', views.Logout, name="logout"),

    #path('', views.dashboard, name='dashboard'),
    #path('', include('django.contrib.auth.urls')),
    path(_('registers/'), views.register, name='registers'),
    #path('edit/', views.edit, name='edit'),

    path('users_list/', views.user_lists, name='user_lists'),
    #path('users/follow/', views.user_follow, name='user_follow'),
    path('users/<username>/', views.user_detail, name='user_detail'),

    #     profile
    path(_('profile/<int:myid>/'), views.MyProfile, name="profile"),
    #path(_('edit_profile/'), views.edit_profile, name="edit_profile"),
    path(_('user_profile/<int:myid>/'), views.user_profile, name="user_profile"),

        # User Managent
    #path(_('user_details/<int:id>'), views.user_details, name="user_details"),
    path(_('user_detailed/<int:id>'), views.user_detailed, name="user_detailed"),

    # Reset Password
    path('change-password/', UserPasswordChangeView.as_view(), name='change_password'),
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),

    
    
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_user, name='register'),
    
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:pk>/permissions/', views.manage_user_permissions, name='manage_user_permissions'),
    path('users/<int:pk>/toggle-active/', views.toggle_user_active, name='toggle_user_active'),
    path('users/<int:pk>/change-password/', views.change_user_password, name='change_user_password'),
    
    # Forgot Password
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
    ), name='password_reset'),
    
    # path('password-reset/', views.DebugPasswordResetView.as_view(
    #     template_name='registration/password_reset_form.html'
    # ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

]
