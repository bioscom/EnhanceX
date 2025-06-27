import traceback
from django.core.mail import mail_admins
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now


class ErrorEmailMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'AnonymousUser'
        path = request.path
        method = request.method
        headers = '\n'.join(f"{k}: {v}" for k, v in request.headers.items())
        timestamp = now().strftime('%Y-%m-%d %H:%M:%S')
        referer = request.META.get('HTTP_REFERER', 'N/A')
        user_agent = request.META.get('HTTP_USER_AGENT', 'N/A')

        traceback_info = traceback.format_exc()

        message = f"""
500 Internal Server Error Caught by Middleware
=============================================

Time: {timestamp}
User: {user}
Path: {path}
Method: {method}
Referer: {referer}
User-Agent: {user_agent}

Headers:
{headers}

Traceback:
{traceback_info}
"""

        # Send the email
        mail_admins(
            subject='[Django] Unhandled Exception (500)',
            message=message,
            fail_silently=True
        )

        # Redirect the user to the homepage
        return redirect('/en/home') # Change 'home' to the name of your URL pattern