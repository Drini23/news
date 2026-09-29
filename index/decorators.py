from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.views import redirect_to_login
from .access import has_active_subscription


def paywall(view_func):
    """
    Gate a view behind an active subscription.
    - Anonymous users → login page
    - Active subscribers → allow
    - Everyone else → /pricing/
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        if has_active_subscription(request.user):
            return view_func(request, *args, **kwargs)

        return redirect("pricing")

    return wrapper