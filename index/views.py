import stripe
from datetime import datetime, timezone as dt_timezone
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import Subscription
from .access import has_active_subscription


# =========================================================
#  STRIPE MODE HELPERS  (test locally, live on Railway)
# =========================================================

def stripe_config():
    """Return (api_key, recurring_price_id, webhook_secret) based on DEBUG."""
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
    """Set stripe.api_key globally. Returns the key."""
    key, _, _ = stripe_config()
    if not key:
        raise RuntimeError(
            f"Stripe API key is empty. DEBUG={settings.DEBUG}. "
            f"Check your environment variables."
        )
    stripe.api_key = key
    print(f"💳 [stripe] mode={'TEST' if settings.DEBUG else 'LIVE'} key={key[:8]}...")
    return key


# =========================================================
#  HELPERS
# =========================================================

def get_or_create_stripe_customer(user):
    configure_stripe()

    sub, _ = Subscription.objects.get_or_create(user=user)
    if sub.stripe_customer_id:
        return sub.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": user.id, "username": user.username},
    )
    sub.stripe_customer_id = customer.id
    sub.save()
    return customer.id


def _get_period_end(stripe_sub):
    """Return period end timestamp. Handles old and new Stripe SDKs."""
    try:
        return stripe_sub.items().data[0].current_period_end
    except (AttributeError, TypeError, IndexError):
        try:
            return stripe_sub.current_period_end
        except AttributeError:
            return None


# =========================================================
#  CHECKOUT — SUBSCRIPTION
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
            f"Check STRIPE_RECURRING_PRICE_ID{' _TEST' if settings.DEBUG else ''}."
        )

    customer_id = get_or_create_stripe_customer(request.user)

    base_success = request.build_absolute_uri(reverse("success"))
    base_cancel = request.build_absolute_uri(reverse("cancel"))

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1,
        }],
        customer=customer_id,
        success_url=base_success + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=base_cancel,
        subscription_data={"metadata": {"user_id": request.user.id}},
        metadata={"user_id": request.user.id},
    )
    return redirect(session.url)


# =========================================================
#  SUCCESS PAGE
# =========================================================

@login_required
def success_page(request):
    configure_stripe()

    session_id = request.GET.get("session_id", "")
    print("🔍 [success] session_id from URL:", session_id)

    if session_id and not session_id.startswith("{CHECKOUT"):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            print("🔍 [success] payment_status:", session.payment_status)
            print("🔍 [success] subscription:", session.subscription)
            print("🔍 [success] customer:", session.customer)

            sub, _ = Subscription.objects.get_or_create(user=request.user)

            if not sub.stripe_customer_id:
                sub.stripe_customer_id = session.customer
                sub.save()

            if session.subscription:
                stripe_sub = stripe.Subscription.retrieve(session.subscription)
                print("🔍 [success] stripe_sub.status:", stripe_sub.status)

                period_end_ts = _get_period_end(stripe_sub)
                print("🔍 [success] period_end:", period_end_ts)

                sub.plan_type = "recurring"
                sub.stripe_subscription_id = stripe_sub.id
                sub.status = stripe_sub.status
                sub.auto_renew = True

                if period_end_ts:
                    sub.current_period_end = datetime.fromtimestamp(
                        period_end_ts, tz=dt_timezone.utc
                    )

                sub.save()
                print("✅ [success] SAVED. is_active:", sub.is_active)

        except stripe.StripeError as e:
            print("❌ [success] Stripe error:", e)
        except Exception as e:
            print("❌ [success] Error:", e)
    else:
        print("⚠️ [success] No valid session_id — skipping sync")

    return render(request, "index/success.html")


# =========================================================
#  CANCEL / PRICING
# =========================================================

def cancel_page(request):
    return render(request, "index/cancel.html")


def pricing(request):
    return render(request, "index/pricing.html")


# =========================================================
#  CUSTOMER PORTAL
# =========================================================

@login_required
def customer_portal(request):
    configure_stripe()

    sub = get_object_or_404(Subscription, user=request.user)
    if not sub.stripe_customer_id:
        return redirect("pricing")

    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=request.build_absolute_uri(reverse("success")),
    )
    return redirect(portal.url)


# =========================================================
#  WEBHOOK  (with signature verification)
# =========================================================

@csrf_exempt
@require_POST
def stripe_webhook(request):
    configure_stripe()
    _, _, webhook_secret = stripe_config()

    if not webhook_secret:
        print("⚠️ [webhook] no webhook secret configured — rejecting")
        return HttpResponse(status=400)

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    # Verify the request actually came from Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        print("❌ [webhook] invalid payload:", e)
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError as e:
        print("❌ [webhook] invalid signature:", e)
        return HttpResponse(status=400)

    event_type = event["type"]
    data = event["data"]["object"]

    print(f"🔔 [webhook] verified event: {event_type}")

    # ---------- Checkout completed ----------
    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        sub = Subscription.objects.filter(stripe_customer_id=customer_id).first()
        if sub and data.get("subscription"):
            stripe_sub = stripe.Subscription.retrieve(data["subscription"])
            period_end_ts = _get_period_end(stripe_sub)

            sub.plan_type = "recurring"
            sub.stripe_subscription_id = stripe_sub.id
            sub.status = stripe_sub.status
            sub.auto_renew = True

            if period_end_ts:
                sub.current_period_end = datetime.fromtimestamp(
                    period_end_ts, tz=dt_timezone.utc
                )

            sub.save()

    # ---------- Subscription created / updated ----------
    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        sub = Subscription.objects.filter(stripe_subscription_id=data.get("id")).first()
        if not sub:
            sub = Subscription.objects.filter(stripe_customer_id=data.get("customer")).first()
        if sub:
            period_end_ts = _get_period_end(data)

            sub.plan_type = "recurring"
            sub.stripe_subscription_id = data.get("id")
            sub.status = data.get("status")
            sub.auto_renew = data.get("status") in ("active", "trialing")

            if period_end_ts:
                sub.current_period_end = datetime.fromtimestamp(
                    period_end_ts, tz=dt_timezone.utc
                )

            sub.save()

    # ---------- Subscription canceled ----------
    elif event_type == "customer.subscription.deleted":
        sub = Subscription.objects.filter(stripe_subscription_id=data.get("id")).first()
        if sub:
            sub.status = "canceled"
            sub.auto_renew = False
            sub.save()

    # ---------- Payment failed ----------
    elif event_type == "invoice.payment_failed":
        sub = Subscription.objects.filter(stripe_customer_id=data.get("customer")).first()
        if sub:
            sub.status = "past_due"
            sub.save()

    return HttpResponse(status=200)


@login_required
def profile(request):
    """Private profile page for the currently logged-in user."""
    sub, _ = Subscription.objects.get_or_create(user=request.user)

    # Whether the user currently has active access
    is_active = has_active_subscription(request.user)

    # A special flag for you / staff
    is_owner = request.user.is_superuser or request.user.is_staff

    context = {
        "sub": sub,
        "is_active": is_active,
        "is_owner": is_owner,
        "has_customer_id": bool(sub.stripe_customer_id),
    }
    return render(request, "index/profile.html", context)