from django.urls import path
from . import views

urlpatterns = [
    path("subscribe/recurring/", views.subscribe_recurring, name="subscribe_recurring"),
    path("pricing/", views.pricing, name="pricing"),
    path("success/", views.success_page, name="success"),
    path("cancel/", views.cancel_page, name="cancel"),
    path("customer-portal/", views.customer_portal, name="customer_portal"),
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
]