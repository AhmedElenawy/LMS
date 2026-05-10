from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.conf import settings
from rest_framework.exceptions import ValidationError


from decimal import Decimal

        
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    usage_limit = models.IntegerField(default=1)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    

    def __str__(self):
        return self.code
    
    def is_valid(self, user):
        now = timezone.now()
        if not user:
            raise ValidationError("User is not provided")
        user_usage = self.coupon_usages.filter(user=user).count()
        if now < self.valid_from:
            raise ValidationError("Coupon is not active yet")
        elif now > self.valid_to:
            raise ValidationError("Coupon is expired")
        elif not self.active:
            raise ValidationError("Coupon is not active")
        elif user_usage >= self.usage_limit:
            raise ValidationError("Coupon usage limit reached")
        return True
    

class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, related_name='coupon_usages')
    used_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.coupon.code}"

