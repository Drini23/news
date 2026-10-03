from django.contrib import admin

from index import models
from .models import Subscription

# Register your models here.

@admin.register(models.Subscription)
class Subscription(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at',  'plan_type', 'status', 'current_period_end', 'auto_renew')
    list_filter = ( 'plan_type', 'status', 'auto_renew')
    search_fields = ('user__username', 'user__email', 'stripe_customer_id', 'stripe_subscription_id', 'stripe_payment_intent_id')

    
