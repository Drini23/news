from django.urls import path
from . import views

urlpatterns = [
    path("create-checkout-session/", views.create_checkout_session, name="create_checkout_session"),
    path("success/", views.success_page, name="success"),
    path("cancel/", views.cancel_page, name="cancel"),
    #path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
]
