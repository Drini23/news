def has_active_subscription(user):
    if not user.is_authenticated:
        return False

    # Superusers and staff always have access (owner / admin accounts)
    if user.is_superuser or user.is_staff:
        return True

    sub = getattr(user, "subscription", None)
    return bool(sub and sub.is_active)