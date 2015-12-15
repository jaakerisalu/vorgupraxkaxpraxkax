import json
from django.shortcuts import render
from django.views.generic import TemplateView

from accounts.models import User

"""
?firstname=
?lastname=
?personalcode=
"""


class ApiView(TemplateView):

    template_name = 'api.html'

    def get_context_data(self, **kwargs):

        context = super(ApiView, self).get_context_data(**kwargs)

        first_name = ''
        last_name = ''
        personal_code = ''

        if self.request.method == 'GET':

            users = []

            if 'all' in self.request.GET:
                users = User.objects.all()
                context['users'] = json.dumps([u.serialize() for u in users])
                return context

            if 'firstname' in self.request.GET:
                first_name = self.request.GET['firstname']

            if 'lastname' in self.request.GET:
                last_name = self.request.GET['lastname']

            if 'personalcode' in self.request.GET:
                personal_code = self.request.GET['personalcode']


        if first_name != '':
            users = User.objects.filter(first_name=first_name)

        if last_name != '':
            users = User.objects.filter(last_name=last_name)

        if first_name != '' and last_name != '':
            users = User.objects.filter(first_name=first_name).filter(last_name=last_name)

        if personal_code != '':
            users = User.objects.filter(personal_code=personal_code)

        print(users)

        context['users'] = json.dumps([u.serialize() for u in users])

        return context

