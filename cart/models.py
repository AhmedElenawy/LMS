from django.db import models

# Create your models here.
from django.conf import settings

from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal

from course.models import Course
from coupon.models import Coupon


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, )
    def discount(self):
        if self.coupon and self.coupon.is_valid(self.user):
            discount = self.coupon.discount / Decimal(100) * self.get_total_price()
            max_discount = Decimal(self.coupon.max_discount)
            if discount > max_discount:
                discount = max_discount
            return discount
        return Decimal('0.00')

    def get_total_price(self):
        return sum(item.course.price for item in self.items.all())
    
    def get_total_price_after_discount(self):
        return self.get_total_price() - self.discount()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    #  only one course in cart
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'course'], name='unique_cart_item')
        ]
