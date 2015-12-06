from django.contrib.auth.views import login as django_login
from django.http import HttpResponseRedirect
from accounts.forms import LoginForm


def login(request):

    if request.user.is_authenticated():
        return HttpResponseRedirect("/")

    response = django_login(request, template_name='accounts/login.html', authentication_form=LoginForm)

    return response
