def has_active_subscription(user):
    if not user.is_authenticated:
        return False
    sub = getattr(user, "subscription", None)
    return bool(sub and sub.is_active)