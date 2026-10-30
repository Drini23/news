from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import format_html

from index import models


# ==================================================
# SUBSCRIPTION ADMIN
# ==================================================

@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'created_at',
        'updated_at',
        'plan_type',
        'status',
        'current_period_end',
        'auto_renew',
    )

    list_filter = (
        'plan_type',
        'status',
        'auto_renew',
    )

    search_fields = (
        'user__username',
        'user__email',
        'stripe_customer_id',
        'stripe_subscription_id',
        'stripe_payment_intent_id',
    )


# ==================================================
# USER ADMIN
# ==================================================

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):

    list_display = (
        'username',
        'email',
        'online_status',
        'last_seen',
        'date_joined',
        'last_login',
        'is_active',
        'is_staff',
    )

    list_display_links = ('username',)

    ordering = ('-date_joined',)

    list_filter = (
        'is_active',
        'is_staff',
        'date_joined',
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )

    date_hierarchy = 'date_joined'

    list_per_page = 50

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('activity')

    @admin.display(description='Online Status')
    def online_status(self, obj):

        activity = getattr(obj, 'activity', None)

        if activity and activity.last_seen >= timezone.now() - timedelta(minutes=5):
            return format_html(
                '<span style="color: #16a34a; font-weight: bold;">● Online</span>'
            )

        return format_html(
            '<span style="color: #dc2626; font-weight: bold;">● Offline</span>'
        )

    @admin.display(description='Last Activity')
    def last_seen(self, obj):

        activity = getattr(obj, 'activity', None)

        if activity:
            return activity.last_seen

        return 'Never'