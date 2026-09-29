from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Subscription(models.Model):
    PLAN_TYPE_CHOICES = [
        ("recurring", "Recurring (auto-renews)"),
        ("one_time", "One-time (30 days)"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)

    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, default="incomplete")
    current_period_end = models.DateTimeField(blank=True, null=True)
    auto_renew = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        if self.status not in ("active", "trialing"):
            return False
        if self.current_period_end and self.current_period_end < timezone.now():
            return False
        return True

    def __str__(self):
        return f"{self.user.email} — {self.status}"