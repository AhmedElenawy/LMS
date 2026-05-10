from django.urls import path, include

from . import views, webhooks


app_name = 'payment'

urlpatterns = [
    path('payment/process/', views.PaymentProcessView.as_view(), name='payment-process'),
    path('payment/success/', views.payment_success.as_view(), name='payment-success'),
    path('payment/cancel/', views.payment_cancel.as_view(), name='payment-cancel'),
    path('payment/webhook/', webhooks.stripe_webhook, name='stripe-webhook',),

]