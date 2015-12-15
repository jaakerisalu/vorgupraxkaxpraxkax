from django.contrib import admin
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from accounts.models import *

from accounts.models import User


class UserChangeForm(auth_forms.UserChangeForm):
    # Hackish variant of builtin UserChangeForm with no username
    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)


class UserCreationForm(auth_forms.UserCreationForm):
    # Hackish variant of builtin UserCreationForm with email instead of username
    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name',
                                         'personal_code', 'email', 'avatar_url')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    list_display = ('id', 'email', 'username', 'is_staff')
    search_fields = ('email', 'username')
    ordering = ('email',)

    form = UserChangeForm
    add_form = UserCreationForm

admin.site.register(User, CustomUserAdmin)
