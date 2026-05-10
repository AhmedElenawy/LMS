from django.db import models

# Create your models here.
from django.conf import settings

from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal

from course.models import Course
from coupon.models import Coupon

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        PAID = 'paid'
        CANCELLED = 'cancelled'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='orders', null=True)

    
    status = models.CharField(choices=Status, default=Status.PENDING, max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    payment_id = models.CharField(max_length=250, null=True)
    session_id = models.CharField(max_length=250, null=True, blank=True)
    payment_method = models.CharField(max_length=250, null=True, blank=True)


    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["-created"])]

    def __str__(self):
        return self.user.first_name
    
    
    # def discount(self):
    #     # if self.discount_amount > 0:
    #     #     return (self.discount_amount / Decimal(100)) * self.get_total_price()
    #     return self.discount_amount

    def get_total_price(self):
        return sum(item.price for item in self.order_items.all() )
    
    def get_total_price_after_discount(self):
        return self.get_total_price() - self.discount_amount
    
    def get_payment_url(self):
        if self.payment_id:
            if "pi_" in self.payment_id:
                if '_test_' in settings.STRIPE_SECRET_KEY:
                    return f"https://dashboard.stripe.com/test/payments/{self.payment_id}"
                return f"https://dashboard.stripe.com/payments/{self.payment_id}"
            else:
                return f"https://eg.dashboard.paymob.com/transaction/{self.payment_id}"
        return ""



class OrderItems(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    item = models.ForeignKey(Course, on_delete=models.SET_NULL, related_name="product_orders", null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    


    
