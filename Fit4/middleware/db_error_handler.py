# Fit4/middleware/db_error_handler.py
from django.db import DatabaseError
from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect

class DatabaseErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except DatabaseError:
            return render(request, 'errors/database_error.html', status=500)
        return response
    
    'Fit4.middleware.db_error_handler.DatabaseErrorMiddleware',
    

class LogoutAnonymousUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the user is anonymous AND trying to access a protected page
        if request.user.is_anonymous and request.path not in [reverse('account:login_page'), reverse('account:logout')]:
            # Optional: only trigger for authenticated-only paths
            if not request.path.startswith('/static/'):  # skip static/media
                messages.warning(request, "Session expired. Please log in again.")
                return redirect('account:login_page')

        return self.get_response(request)