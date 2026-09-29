from django.conf import settings


def paywall_context(request):
    if not request.user.is_authenticated:
        return {"free_views_left": settings.FREE_VIEW_LIMIT, "is_subscribed": False}

    sub = getattr(request.user, "subscription", None)
    is_subscribed = bool(sub and sub.is_active)
    used = request.user.content_views.count()
    return {
        "free_views_left": max(0, settings.FREE_VIEW_LIMIT - used),
        "is_subscribed": is_subscribed,
    }