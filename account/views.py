from django.shortcuts import render

# Create your views here.
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

# from myblog.models import BlogPost
from Fit4.models import *
#from .models import Profile
from .forms import LoginForm, PasswordResetForm, UserRegistrationForm, UserEditForm, CustomPasswordChangeForm, UserGroupsForm #, ProfileForm, ProfileEditForm
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from django.http import JsonResponse
from django.views.decorators.http import require_POST
#from common.decorators import ajax_required
#from .models import Contact
from django.core.mail import send_mail
#from verify_email.email_handler import send_verification_email
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from user_visit.models import *
import datetime
from datetime import datetime
from smtplib import SMTPException
from django.contrib.auth import get_user_model
import traceback

from django.contrib.auth import authenticate 
from django.contrib.auth.middleware import *
from django.contrib import auth
from django.contrib.auth.middleware import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.utils.functional import SimpleLazyObject

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm


# @login_required
def user_login(request):
    # Ask ChartGpt "How to do single sign on in an intranet application in Django"
    #username = request.META['REMOTE_USER']
    #user = request.META.get('REMOTE_USER')
    #return HttpResponse(f"Authenticated user: {user}")
    try:
        #AUTH_LDAP_USER_ATTR_MAP
        #username = request.settings.AUTH_LDAP_USER_ATTR_MAP.username
        username = request.META['USERNAME']
	    #username = request.META.get('REMOTE_USER')
        if User.objects.get(username=username):
            request.user = User.objects.get(username=username)
            #messages.success(request, "Welcome!!!")
            return redirect("/en/home")
        else:
            messages.error(request, 'You do not have access to EnhanceX, contact the administrator!!!')
            return redirect("/login_page")
        #messages.success(request, "Welcome!!!")
    except Exception as e:
        print(traceback.format_exc())
    return redirect("/login_page")

def user_login2(request):
    try:
        if request.method == 'POST':
            form = LoginForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                username=cd['username']
                password=cd['password']
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        #next_url = request.POST.get('next') or request.GET.get('next') or '/en/home'
                        #return redirect(next_url)
                        # Redirect to home page which contains all users Initiatives.
                        return redirect("/en/home")
                    else:
                        # Return an 'invalid login' error message.
                        messages.error(request, 'You do not have access to EnhanceX, or your session has expired. Contact the system administrator.')
                        return redirect("/login_page")
                else:
                    messages.error(request, 'You do not have access to EnhanceX. Contact the system administrator.')
                    return redirect("/login_page")
        else:
            #next_url = request.GET.get('next', '/')
            form = LoginForm()
    except Exception as e:
         print(traceback.format_exc())
    return render(request, 'account/login.html', {'form': form})

#@login_required(login_url='account:login')
def login_as(request, username):
    try:
        if not request.user.is_superuser:
            return HttpResponseForbidden("Admins Only")
            # retrieve user with the usename
        user = get_object_or_404(User, username=username)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        if not user.is_active:
            raise Exception("User account is inactive.")
        else:
            login(request, user)
            return redirect("/en/home")

        # o = User.objects.get(username=username)
        # password = o.password #'admin'
        # user = authenticate(request, username=username, password=password)
        # if user is not None:
        #     if user.is_active:
        #         login(request, user)
        #         messages.info(request, 'Logged in as ' + str(user.first_name) + ', ' + str(user.last_name) + '( '+ user.email +')'  'Log out as ' + "<a href='/en/login_page'>" + str(user.first_name) + ', ' + str(user.last_name) + '</a>' )
        #         return redirect("/en/home")
        #     else:
        #         # Return an 'invalid login' error message.
        #         messages.error(request, 'You do not have access to EnhanceX, contact the administrator!!!')
        #         return redirect("/login_page")
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'account/login.html')


def user_detailed(request, id):
    try:
        oUser = get_user_model().objects.get(id=id)
        obj = UserVisit.objects.filter(user_id=id).order_by('timestamp')
        # if request.method == "POST":
        #     #initiative.author = get_user_model().objects.get(id=initiative.author)
        #     #initiative.save()
        #     return redirect('/en/initiative/'+ str(id))
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'account/UserDetails.html', {'oUser': oUser, 'obj':obj})
    
def Logout(request):
    logout(request)
    #request.session.flush() # Ensures session is completely cleared
    #messages.success(request, "You have been successfully logged out.")
    return redirect('/en')

def send_login_mail(request, user):
    obj = UserVisit.objects.filter(user_id=user.id).order_by('timestamp').last()
   
    subject = "Login Notification"
    datetime_obj = datetime.strptime(str(obj.timestamp),  "%Y-%m-%d %H:%M:%S.%f%z")
    
    source = ''
    if 'iPhone' in obj.ua_string:
        source = 'Mobile iPhone'
    elif 'Windows' in obj.ua_string:
        source = 'desktop'
    elif 'Android' in obj.ua_string:
        source = 'Mobile Android'
    
    message = "Dear user,\n \n"
    message += "You logged in at "+ str(datetime_obj.strftime('%I:%H %p')) + " on " + str(datetime.strptime(str(datetime_obj), "%Y-%m-%d %H:%M:%S.%f%z").date()) + " from the following "+ source +" device:\n"
    message += "User Agent: " + obj.ua_string + "\n"
    message += "IP Address: " + obj.remote_addr + "\n \n" 
    #message += "https://acrossglobes.com/"
    
    try:
        sendermail = request.user.email
        receipientmail = [request.user.email]
        send_mail(subject, message, sendermail, receipientmail)
    except SMTPException as e:
         return JsonResponse({'status':'error'})
    return JsonResponse({'status':'ok'})

# @login_required
# def dashboard(request):
#     return render(request, 'account/dashboard.html', {'section': 'dashboard'})

#region ========================= User Management from Django Panel ======================================

def staff_only(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(staff_only)
def user_list(request):
    try:
        query = request.GET.get("q")
        users = User.objects.all()
        if query:
            users = users.filter(username__icontains=query)
        
        users = users.order_by('username')  # Must be done here last
        
        # paginator = Paginator(users, 100)  # 10 users per page
        # page = request.GET.get("page")
        # users = paginator.get_page(page)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'account/user_list.html', {'users': users})


@user_passes_test(staff_only)
def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User registered successfully.")
            #return redirect('users/' + str(form.id) + '/edit/')
            return redirect('en/users/') #users/<int:pk>/edit/
    else:
        form = UserCreationForm()
    return render(request, 'account/register.html', {'form': form})

@user_passes_test(staff_only)
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect('en/users/')
    else:
        form = UserChangeForm(instance=user)
    return render(request, 'account/edit_user.html', {'form': form, 'user_obj': user})

@user_passes_test(staff_only)
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "User deleted.")
        return redirect('en/users/')
    return render(request, 'account/confirm_delete.html', {'user_obj': user})

@user_passes_test(staff_only)
def change_user_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password changed.")
            return redirect('en/users/')
    else:
        form = PasswordChangeForm(user)
    return render(request, 'account/change_password.html', {'form': form, 'user_obj': user})


@user_passes_test(staff_only)
def manage_user_permissions(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserGroupsForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Groups/permissions updated.")
            return redirect('en/users/')
    else:
        form = UserGroupsForm(instance=user)
    return render(request, 'account/manage_permissions.html', {'form': form, 'user_obj': user})

@user_passes_test(staff_only)
def toggle_user_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {status}.")
    return redirect('en/users/')

#endregion =================================================================================================

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            #inactive_user = send_verification_email(request, form)
            new_user = form.save(commit=False) # Create a new user object but avoid saving it yet
            new_user.set_password(form.cleaned_data['password']) # Set the chosen password
            new_user.save() # Save the User object
            #Profile.objects.create(user=new_user) # Create the user profile
            return render(request, 'account/register_done.html', {'new_user': new_user})
            #messages.success(request, 'You are successfully registered and an email has been sent to your email address, use the link in the e-mail to confirm your registration.')
            #return redirect("/")
        else:
            messages.error(request, 'Not sucessful, try again!')
            #return redirect("/")
    else:
        form = UserRegistrationForm()
    return render(request, 'account/register.html', {'user_form': form})


class UserPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('password_change_done')
    form_class = CustomPasswordChangeForm # You can also use Django’s default

# @login_required
# def edit(request):
#     if request.method == 'POST':
#         user_form = UserEditForm(instance=request.user, data=request.POST)
#         profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
#         if user_form.is_valid() and profile_form.is_valid():
#             user_form.save()
#             profile_form.save()
#             messages.success(request, 'Profile updated successfully')
#             #return redirect("/")
#         else:
#             messages.error(request, 'Error updating your profile')
#             #return redirect("/")
#     else:
#         user_form = UserEditForm(instance=request.user)
#         profile_form = ProfileEditForm(instance=request.user.profile)
#     return render(request, 'account/edit.html', {'user_form': user_form, 'profile_form': profile_form})


# def edit_profile(request):
#     try:
#         profile = request.user.profile
#     except Profile.DoesNotExist:
#         profile = Profile(user=request.user)
#     if request.method == "POST":
#         form = ProfileForm(data=request.POST, files=request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Your profile update was successful.")
#             return redirect("/")
#             #alert = True
#             #return render(request, "account/partial_edit_profile.html", {'alert': alert})
#     else:
#         form = ProfileForm(instance=profile)
#     return render(request, "account/partial_edit_profile.html", {'form': form})

@login_required
def user_lists(request):
    users = User.objects.filter(is_active=True)
    return render(request, 'account/user/partial_list.html', {'section': 'people', 'users': users})

@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    return render(request, 'account/user/partial_detail.html', {'section': 'people', 'user': user})


def user_profile(request, myid):
    object_list = Initiative.objects.filter(author_id=myid).filter(parent_id__isnull=True).order_by('-dateTime')
    thisUser = User.objects.get(id=myid)

    # Paginate user's post list
    no_of_pages = Paginating.objects.get()
    paginator = Paginator(object_list, no_of_pages.number_of_pages)  # 3 posts in each page
    page = request.GET.get('page')
    try:
        post = paginator.get_page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        post = paginator.get_page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        #post = paginator.page(paginator.num_pages)
        post.adjusted_elided_pages = paginator.get_elided_page_range(paginator.num_pages)

    return render(request, "account/partial_user_profile.html", {'post': post, 'thisUser':thisUser})


def MyProfile(request, myid):
    object_list = Initiative.objects.filter(author_id=myid).filter(parent_id__isnull=True).order_by('-dateTime')

    # Paginate user's post list
    no_of_pages = Paginating.objects.get()
    paginator = Paginator(object_list, no_of_pages.number_of_pages)  # 3 posts in each page
    page = request.GET.get('page')
    try:
        post = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        post = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        #post = paginator.page(paginator.num_pages)
        post.adjusted_elided_pages = paginator.get_elided_page_range(page)

    return render(request, "account/partial_profile.html", {'post': post})


def password_change(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password sucessfuly changed")
            return redirect('/')
            #return render(request, "registration/password_reset_form.html", {'form': form})
            #return HttpResponse(status=204, headers={'HX-Trigger': json.dumps({"movieListChanged": None, "showMessage": f"{new_user.first_name} added." })})
    else:
        form = PasswordResetForm()
    return render(request, "registration/password_reset_form.html", {'form': form})