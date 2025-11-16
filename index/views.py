from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

stripe.api_key = settings.STRIPE_SECRET_KEY_TEST

@login_required
def create_checkout_session(request):
    # Use a Stripe price ID (starts with "price_"). A product ID (starts with "prod_") won't work here.
    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{
            "price": "price_1RUaYVQ7xrYURdvSG0SsnZ0C",  # replace with your actual price id
            "quantity": 1,
        }],
        customer_email=request.user.email,
        success_url="http://127.0.0.1:8000/index/success/",
        cancel_url="http://127.0.0.1:8000/",
    )

    return redirect(session.url)




def success_page(request):
    return render(request, "index/success.html")

def cancel_page(request):
    return HttpResponse("Payment canceled.")