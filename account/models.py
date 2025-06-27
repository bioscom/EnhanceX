from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from phone_field import PhoneField

# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
#     image = models.ImageField(upload_to='profile_pics/%Y/%m/%d/', blank=True, null=True)
#     #name = models.TextField(blank=True, null=True)
#     bio = models.TextField(_('bio'), blank=True, null=True)
#     phone_no = PhoneField(_('phone_no'), blank=True, null=True)
#     facebook = models.CharField(_('facebook'), max_length=300, blank=True, null=True)
#     instagram = models.CharField(_('instagram'), max_length=300, blank=True, null=True)
#     linkedin = models.CharField(_('linkedin'), max_length=300, blank=True, null=True)
    
#     def __str__(self):
#         return f'Profile for user {self.user.username}'
#         #return str(self.user)

# # ========== Tracking User Actions . Follow System ========= 
# class Contact(models.Model):
#     user_from = models.ForeignKey('auth.User', related_name='rel_from_set', on_delete=models.CASCADE)
#     user_to = models.ForeignKey('auth.User', related_name='rel_to_set', on_delete=models.CASCADE)
#     created = models.DateTimeField(auto_now_add=True, db_index=True)

#     class Meta:
#         ordering = ('-created',)

#     def __str__(self):
#         return f'{self.user_from} follows {self.user_to}'     
    
# # Add following field to User dynamically
# user_model = get_user_model()
# user_model.add_to_class('following', models.ManyToManyField('self', through=Contact, related_name='followers', symmetrical=False))


# === Codes to migrate models into database === #
# python manage.py makemigrations
# python manage.py migrate