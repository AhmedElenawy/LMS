import stripe
from django.conf import settings
from order.models import Order
from course.models import Course, Enrollment
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse ,HttpResponseForbidden
from .tasks import after_payment
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    # define event out of scope
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        #  invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # invalid signnature
        return HttpResponse(status=400)
    
    if event.type == 'checkout.session.completed':
        #  this is the session i sent
        session = event.data.object
        if session.mode == 'payment' and session.payment_status == 'paid':
            after_payment.delay(session.client_reference_id, session.payment_intent)
    return HttpResponse(status=200)
    
