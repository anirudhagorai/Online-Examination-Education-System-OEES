# /home/workdir/attachments/decorators.py
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """
    Secure admin-only decorator.
    Handles both normal requests (redirect) and AJAX/fetch requests (JSON 403).
    """
    @login_required(login_url='/auth/admin')
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check admin privileges
        is_admin = (
            getattr(request.user, 'is_superuser', False) or
            (hasattr(request.user, 'profile') and getattr(
                request.user.profile, 'role', None) == 'admin')
        )

        if is_admin:
            return view_func(request, *args, **kwargs)

        # AJAX request → return JSON instead of redirect (prevents 302 error)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Admin access required.'
            }, status=403)

        # Normal request
        messages.error(
            request, "Unauthorized access. Administrator privileges required.")
        return redirect('admin_login')

    return _wrapped_view
