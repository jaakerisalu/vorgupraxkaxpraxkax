import urllib

from django.core.files.base import ContentFile
from social.backends.facebook import FacebookOAuth2
from social.backends.google import GoogleOAuth2


def get_avatar_url(request, backend, response, *args, **kwargs):
    """Pipeline to get user avatar from Twitter/FB via django-social-auth"""
    avatar_url = ''
    if isinstance(backend, FacebookOAuth2):
        avatar_url = 'http://graph.facebook.com/%s/picture?type=large' \
                     % response['id']

    if isinstance(backend, GoogleOAuth2):
        if response.get('image') and response['image'].get('url'):
            avatar_url = response['image'].get('url')

    user = kwargs['user']
    user.avatar_url = avatar_url
    user.save()
    return
