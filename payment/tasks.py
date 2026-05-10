from celery import shared_task
from django.core.mail import EmailMessage, EmailMultiAlternatives
from smtplib import SMTPException

from django.core.files.base import ContentFile
from order.models import Order

from course.models import Enrollment, Course
import weasyprint
from django.contrib.staticfiles import finders

from django.template.loader import render_to_string

from django.shortcuts import get_object_or_404

@shared_task(bind=True,
    autoretry_for=(SMTPException, ConnectionError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True)
def send_success_email(self, order_id ):
    order = get_object_or_404(Order.objects.select_related('user'), id=order_id)
    
    subject = "Start your new leaning journey"
    text_body = f"congratulations your order has been successfully placed"
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
            <h2 style="color: #333;">Start your new leaning journey</h2>
            <p>congratulations your order has been successfully placed</p>
        </body>
    </html>
    """
    try:
        email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=None,
        to=[order.user.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
    except Exception as e:
        raise
    


@shared_task
def after_payment(client_reference_id, payment_intent):
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('order_items__item'), id=client_reference_id)
    order.status = Order.Status.PAID
    order.payment_id = payment_intent
    order.save()

    for item in order.order_items.all():
        course = item.item
        Enrollment.objects.create(
            student=order.user.student_info,
            course=course
        )