import stripe

from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import Subscription
from .access import has_active_subscription


User = get_user_model()


# =========================================================
# STRIPE CONFIGURATION
# =========================================================

def stripe_config():
    """Return the correct Stripe keys based on DEBUG."""

    if settings.DEBUG:
        return (
            settings.STRIPE_SECRET_KEY_TEST,
            settings.STRIPE_RECURRING_PRICE_ID_TEST,
            settings.STRIPE_WEBHOOK_SECRET_TEST,
        )

    return (
        settings.STRIPE_SECRET_KEY,
        settings.STRIPE_RECURRING_PRICE_ID,
        settings.STRIPE_WEBHOOK_SECRET,
    )


def configure_stripe():
    """Configure Stripe API."""

    key, _, _ = stripe_config()

    if not key:
        raise RuntimeError(
            f"Stripe API key is empty. DEBUG={settings.DEBUG}. "
            "Check your Railway environment variables."
        )

    stripe.api_key = key

    print(
        f"💳 [stripe] mode={'TEST' if settings.DEBUG else 'LIVE'} "
        f"key={key[:8]}..."
    )

    return key


# =========================================================
# GENERAL HELPERS
# =========================================================

def _timestamp_to_datetime(timestamp):
    """Convert a Stripe Unix timestamp to a timezone-aware datetime."""

    if not timestamp:
        return None

    return datetime.fromtimestamp(
        int(timestamp),
        tz=dt_timezone.utc
    )


def _get_period_end(stripe_sub):
    """
    Get subscription period end.

    Supports newer Stripe API responses where the period end
    is available on subscription items.
    """

    if not stripe_sub:
        return None

    # Newer Stripe API structure
    items = stripe_sub.get("items")

    if items:
        item_data = items.get("data", [])

        if item_data:
            period_end = item_data[0].get("current_period_end")

            if period_end:
                return period_end

    # Older Stripe API structure
    return stripe_sub.get("current_period_end")


def _get_invoice_subscription_id(invoice):
    """Extract the subscription ID from a Stripe invoice."""

    # Newer Stripe API structure
    parent = invoice.get("parent") or {}

    subscription_details = (
        parent.get("subscription_details") or {}
    )

    subscription_id = subscription_details.get("subscription")

    if isinstance(subscription_id, dict):
        subscription_id = subscription_id.get("id")

    if subscription_id:
        return subscription_id

    # Older Stripe API structure
    subscription_id = invoice.get("subscription")

    if isinstance(subscription_id, dict):
        subscription_id = subscription_id.get("id")

    return subscription_id


def _find_local_subscription(
    stripe_subscription_id=None,
    customer_id=None,
    user_id=None,
):
    """
    Find the Django Subscription using Stripe IDs.

    If necessary, fall back to the user_id stored in Stripe metadata.
    """

    sub = None

    if stripe_subscription_id:
        sub = Subscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        ).first()

    if not sub and customer_id:
        sub = Subscription.objects.filter(
            stripe_customer_id=customer_id
        ).first()

    if not sub and user_id:
        try:
            user = User.objects.get(pk=int(user_id))

            sub, _ = Subscription.objects.get_or_create(
                user=user
            )

            # Do not attach a different Stripe customer accidentally.
            if (
                customer_id
                and sub.stripe_customer_id
                and sub.stripe_customer_id != customer_id
            ):
                print(
                    "⚠️ [stripe] Customer ID mismatch for user:",
                    user_id
                )
                return None

        except (User.DoesNotExist, ValueError, TypeError):
            print(
                "⚠️ [stripe] Could not find user from metadata:",
                user_id
            )
            return None

    return sub


def _sync_subscription(sub, stripe_sub):
    """Synchronize a Django subscription with the current Stripe record."""

    if not sub or not stripe_sub:
        return

    period_end_ts = _get_period_end(stripe_sub)

    sub.plan_type = "recurring"
    sub.stripe_subscription_id = stripe_sub.id
    sub.stripe_customer_id = stripe_sub.get("customer")
    sub.status = stripe_sub.get("status")

    cancel_at_period_end = stripe_sub.get(
        "cancel_at_period_end",
        False
    )

    sub.auto_renew = (
        sub.status in ("active", "trialing")
        and not cancel_at_period_end
    )

    if period_end_ts:
        sub.current_period_end = _timestamp_to_datetime(
            period_end_ts
        )

    sub.save()

    print(
        "✅ [stripe] Subscription synchronized:",
        sub.user.email,
        "Status:",
        sub.status,
        "Period end:",
        sub.current_period_end,
        "Active:",
        sub.is_active,
    )


# =========================================================
# STRIPE CUSTOMER
# =========================================================

def get_or_create_stripe_customer(user):

    configure_stripe()

    sub, _ = Subscription.objects.get_or_create(
        user=user
    )

    if sub.stripe_customer_id:
        return sub.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        metadata={
            "user_id": str(user.id),
            "username": user.username,
        },
    )

    sub.stripe_customer_id = customer.id
    sub.save()

    print(
        "✅ [stripe] Customer created:",
        customer.id
    )

    return customer.id


# =========================================================
# CHECKOUT — RECURRING SUBSCRIPTION
# =========================================================

@login_required
def subscribe_recurring(request):

    if has_active_subscription(request.user):
        return redirect("success")

    configure_stripe()

    _, price_id, _ = stripe_config()

    if not price_id:
        raise RuntimeError(
            f"Stripe price ID is empty. DEBUG={settings.DEBUG}. "
            "Check your environment variables."
        )

    customer_id = get_or_create_stripe_customer(
        request.user
    )

    success_url = (
        request.build_absolute_uri(reverse("success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )

    cancel_url = request.build_absolute_uri(
        reverse("cancel")
    )

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],

        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],

        customer=customer_id,

        success_url=success_url,
        cancel_url=cancel_url,

        subscription_data={
            "metadata": {
                "user_id": str(request.user.id),
            }
        },

        metadata={
            "user_id": str(request.user.id),
        },
    )

    return redirect(session.url)


# =========================================================
# SUCCESS PAGE
# =========================================================

@login_required
def success_page(request):

    configure_stripe()

    session_id = request.GET.get("session_id", "")

    print(
        "🔍 [success] Session ID:",
        session_id
    )

    if session_id and not session_id.startswith("{CHECKOUT"):

        try:
            session = stripe.checkout.Session.retrieve(
                session_id
            )

            print(
                "🔍 [success] Payment status:",
                session.payment_status
            )

            print(
                "🔍 [success] Subscription:",
                session.subscription
            )

            if session.subscription:

                stripe_sub = stripe.Subscription.retrieve(
                    session.subscription
                )

                sub, _ = Subscription.objects.get_or_create(
                    user=request.user
                )

                customer_id = session.customer

                if (
                    sub.stripe_customer_id
                    and sub.stripe_customer_id != customer_id
                ):
                    print(
                        "⚠️ [success] Stripe customer mismatch"
                    )
                else:
                    sub.stripe_customer_id = customer_id

                    _sync_subscription(
                        sub,
                        stripe_sub
                    )

        except stripe.StripeError as error:
            print(
                "❌ [success] Stripe error:",
                error
            )

        except Exception as error:
            print(
                "❌ [success] Error:",
                error
            )

    else:
        print(
            "⚠️ [success] No valid session ID"
        )

    return render(
        request,
        "index/success.html"
    )


# =========================================================
# CANCEL / PRICING
# =========================================================

def cancel_page(request):
    return render(
        request,
        "index/cancel.html"
    )


def pricing(request):
    return render(
        request,
        "index/pricing.html"
    )


# =========================================================
# CUSTOMER PORTAL
# =========================================================

@login_required
def customer_portal(request):

    configure_stripe()

    sub = get_object_or_404(
        Subscription,
        user=request.user
    )

    if not sub.stripe_customer_id:
        return redirect("pricing")

    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,

        return_url=request.build_absolute_uri(
            reverse("success")
        ),
    )

    return redirect(portal.url)


# =========================================================
# STRIPE WEBHOOK
# =========================================================

@csrf_exempt
@require_POST
def stripe_webhook(request):

    configure_stripe()

    _, _, webhook_secret = stripe_config()

    if not webhook_secret:
        print(
            "❌ [webhook] Missing webhook signing secret"
        )
        return HttpResponse(status=400)

    payload = request.body

    signature = request.META.get(
        "HTTP_STRIPE_SIGNATURE",
        ""
    )

    # -----------------------------------------------------
    # VERIFY STRIPE SIGNATURE
    # -----------------------------------------------------

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            webhook_secret,
        )

    except ValueError as error:
        print(
            "❌ [webhook] Invalid payload:",
            error
        )
        return HttpResponse(status=400)

    except stripe.SignatureVerificationError as error:
        print(
            "❌ [webhook] Invalid signature:",
            error
        )
        return HttpResponse(status=400)

    event_type = event["type"]
    data = event["data"]["object"]

    print(
        "🔔 [webhook] Verified event:",
        event_type
    )

    # -----------------------------------------------------
    # PROCESS EVENTS
    # -----------------------------------------------------

    try:

        # =================================================
        # CHECKOUT COMPLETED
        # =================================================

        if event_type == "checkout.session.completed":

            customer_id = data.get("customer")

            subscription_id = data.get("subscription")

            metadata = data.get("metadata") or {}

            user_id = metadata.get("user_id")

            sub = _find_local_subscription(
                stripe_subscription_id=subscription_id,
                customer_id=customer_id,
                user_id=user_id,
            )

            if sub and subscription_id:

                stripe_sub = stripe.Subscription.retrieve(
                    subscription_id
                )

                _sync_subscription(
                    sub,
                    stripe_sub
                )

        # =================================================
        # SUBSCRIPTION CREATED / UPDATED
        # =================================================

        elif event_type in (
            "customer.subscription.created",
            "customer.subscription.updated",
        ):

            subscription_id = data.get("id")
            customer_id = data.get("customer")

            metadata = data.get("metadata") or {}

            user_id = metadata.get("user_id")

            sub = _find_local_subscription(
                stripe_subscription_id=subscription_id,
                customer_id=customer_id,
                user_id=user_id,
            )

            if sub:

                _sync_subscription(
                    sub,
                    data
                )

        # =================================================
        # SUBSCRIPTION DELETED
        # =================================================

        elif event_type == "customer.subscription.deleted":

            subscription_id = data.get("id")

            sub = Subscription.objects.filter(
                stripe_subscription_id=subscription_id
            ).first()

            if sub:

                sub.status = "canceled"
                sub.auto_renew = False
                sub.save()

                print(
                    "❌ [stripe] Subscription canceled:",
                    sub.user.email
                )

        # =================================================
        # INVOICE PAID — IMPORTANT MONTHLY RENEWAL EVENT
        # =================================================

        elif event_type == "invoice.paid":

            print(
                "💰 [webhook] Processing invoice.paid"
            )

            billing_reason = data.get("billing_reason")

            customer_id = data.get("customer")

            subscription_id = _get_invoice_subscription_id(
                data
            )

            print(
                "🔍 [invoice.paid] Billing reason:",
                billing_reason
            )

            print(
                "🔍 [invoice.paid] Customer:",
                customer_id
            )

            print(
                "🔍 [invoice.paid] Subscription:",
                subscription_id
            )

            # Only process subscription invoices.
            if subscription_id:

                parent = data.get("parent") or {}

                subscription_details = (
                    parent.get("subscription_details") or {}
                )

                metadata = (
                    subscription_details.get("metadata") or {}
                )

                if not metadata:
                    metadata = data.get("metadata") or {}

                user_id = metadata.get("user_id")

                # Retrieve the latest subscription from Stripe.
                stripe_sub = stripe.Subscription.retrieve(
                    subscription_id
                )

                # Stripe subscription metadata is another fallback.
                stripe_metadata = (
                    stripe_sub.get("metadata") or {}
                )

                if not user_id:
                    user_id = stripe_metadata.get("user_id")

                sub = _find_local_subscription(
                    stripe_subscription_id=subscription_id,
                    customer_id=customer_id,
                    user_id=user_id,
                )

                if sub:

                    # Always use the current Stripe subscription
                    # status and billing period.
                    _sync_subscription(
                        sub,
                        stripe_sub
                    )

                    print(
                        "✅ [invoice.paid] User access synchronized:",
                        sub.user.email,
                        "Active:",
                        sub.is_active,
                    )

                else:
                    print(
                        "⚠️ [invoice.paid] No matching Django subscription found"
                    )

            else:
                print(
                    "ℹ️ [invoice.paid] Not a subscription invoice"
                )

        # =================================================
        # PAYMENT FAILED
        # =================================================

        elif event_type == "invoice.payment_failed":

            customer_id = data.get("customer")

            subscription_id = _get_invoice_subscription_id(
                data
            )

            sub = _find_local_subscription(
                stripe_subscription_id=subscription_id,
                customer_id=customer_id,
            )

            if sub:

                sub.status = "past_due"
                sub.save()

                print(
                    "⚠️ [stripe] Payment failed:",
                    sub.user.email
                )

        else:

            print(
                "ℹ️ [webhook] Event not handled:",
                event_type
            )

        return HttpResponse(status=200)

    except Exception as error:

        # Return 500 so Stripe can retry the event.
        print(
            "❌ [webhook] Processing error:",
            event_type,
            str(error)
        )

        return HttpResponse(status=500)


# =========================================================
# USER PROFILE
# =========================================================

@login_required
def profile(request):

    sub, _ = Subscription.objects.get_or_create(
        user=request.user
    )

    is_active = has_active_subscription(
        request.user
    )

    is_owner = (
        request.user.is_superuser
        or request.user.is_staff
    )

    context = {
        "sub": sub,
        "is_active": is_active,
        "is_owner": is_owner,
        "has_customer_id": bool(
            sub.stripe_customer_id
        ),
    }

    return render(
        request,
        "index/profile.html",
        context
    )