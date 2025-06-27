from django.shortcuts import redirect
from django.urls import resolve
from django.conf import settings

EXEMPT_URL_NAMES = [
    'login_page',
    'logout',
    # 'register',
    # 'admin:login',
    # add more named URLs
]

EXEMPT_PATHS = [
    settings.STATIC_URL,
    settings.MEDIA_URL,
] # Optional: skip static/media files


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        try:
            url_name = resolve(path).url_name
        except:
            url_name = None

        # Skip exempt URLs and static/media paths
        if (
            url_name in EXEMPT_URL_NAMES or
            any(path.startswith(p) for p in EXEMPT_PATHS) or
            request.user.is_authenticated
        ):
            return self.get_response(request)

        return redirect(settings.LOGIN_URL) # Make sure this matches your login URL pattern

