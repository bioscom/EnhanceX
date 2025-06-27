from django import forms
from django.contrib.auth.models import User, Group, Permission


from django.contrib.auth.forms import PasswordChangeForm
#from .models import Profile
#from phonenumber_field.formfields import PhoneNumberField

class CustomPasswordChangeForm(PasswordChangeForm):
    pass #You can customise fields if needed

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', )
         

class PasswordResetForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', )
        
        
        
#region ========================= User Management from Django Panel ======================================

class UserGroupsForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = User
        fields = ['groups', 'user_permissions']

#endregion ===============================================================================================