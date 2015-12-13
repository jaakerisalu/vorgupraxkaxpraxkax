# -*- coding: utf-8 -*-

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core import validators
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    # Mostly copied from django.contrib.auth.models.UserManager

    def _create_user(self, username, email, password,
             is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email,
                          is_staff=is_staff, is_active=True, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True,
                                 **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class Gender():
        MALE = 0
        FEMALE = 1
        UNKNOWN = 2
        CHOICES = [(MALE, 'Male'), (FEMALE, 'Female'), (UNKNOWN, 'Unknown')]

    username = models.CharField(_('username'), max_length=30, unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, digits and '
                    '@/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(r'^[\w.@+-]+$', _('Enter a valid username.'), 'invalid')
        ])
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    gender = models.IntegerField(choices=Gender.CHOICES, default=Gender.UNKNOWN)
    birthday = models.DateField(default=timezone.now)
    facebook_id = models.CharField(max_length=30, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    objects = UserManager()

    is_staff = models.BooleanField('staff status', default=False)
    is_active = models.BooleanField('active', default=True)
    date_joined = models.DateTimeField('date joined', default=timezone.now)

    avatar_url = models.CharField(max_length=300, blank=True)

    objects = UserManager()

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        """ ensure instance has usable password when created """
        if not self.pk and self.has_usable_password() is False:
            self.set_password(self.password)

        super(User, self).save(*args, **kwargs)

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username
