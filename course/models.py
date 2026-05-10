from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from .fields import OrderField
from authentication.models import Student, Instructor
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.text import slugify
from datetime import timedelta

# Create your models here.


class Category(MPTTModel):
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', db_index=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class MPTTMeta:
        order_insertion_by = ["title"]
    def __str__(self):
        return self.title
    
class Admin(models.Model):
    admin = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='course_admin_roles')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='admin_course')
    
    can_add    = models.BooleanField(default=False)
    can_edit   = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_view = models.BooleanField(default=False)

    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['admin', 'course'], name='unique_course_admin')
        ]
    
    def __str__(self):
        return f"{self.admin} - {self.course}"
    
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_enrollment')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='course_enrollment')
    date = models.DateTimeField(auto_now_add=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    completed_items = models.ManyToManyField('Content', blank=True, related_name='completed_by_enrollments')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_enrollment')
        ]
    def __str__(self):
        return f"{self.student} enrolled in {self.course}"

class Discount(models.Model):
    discount = models.IntegerField('discount', validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateTimeField('valid from')
    valid_to = models.DateTimeField('valid to')
    active = models.BooleanField('active')

    def is_valid(self):
        now = timezone.now()
        if now < self.valid_from or now > self.valid_to or not self.active:
            return False
        return True         
    
    def __str__(self):
        return f"{self.discount}% from {self.valid_from} to {self.valid_to}"



class Course(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=True, related_name='instructor_courses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='category_courses')
    admins = models.ManyToManyField(Instructor, through='Admin', related_name='course_admins', blank=True)
    students = models.ManyToManyField(Student, through='Enrollment', related_name='course_students', blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    student_count = models.IntegerField(default=0,null=True, blank=True)

    overview = models.TextField(blank=True)
    features = models.TextField(blank=True)
    prequirements = models.TextField()  
    image = models.ImageField(upload_to='course_images', null=True, blank=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def price(self):
        if self.discount and self.discount.is_valid():
            return self.base_price - (self.base_price * self.discount.discount / 100)
        return self.base_price
    
    def get_discount(self):
        if self.discount and self.discount.is_valid():
            return self.discount.discount
        return 0

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # This will forcefully overwrite the slug with the title EVERY time it is saved
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created']
    
class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])

    class Meta:
        ordering = ['order'] 
    def __str__(self):
        return f"{self.order}. {self.title}"
    
class Content(models.Model):
    module = models.ForeignKey(Module, related_name="contents", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, related_name="contents", on_delete=models.CASCADE)
    obj_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'obj_id')
    order = OrderField(blank=True, for_fields=['module'])

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=["content_type", "obj_id"]),
        ]

class ItemBase(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='%(class)s_related', null=True, blank=True)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    content = GenericRelation(Content, content_type_field='content_type', object_id_field='obj_id')

    class Meta:
        abstract = True
        
    def __str__(self):
        return self.title
    
class Text(ItemBase):
    body = models.TextField()

class File(ItemBase):
    file = models.FileField(upload_to='files')

class Image(ItemBase):
    image= models.ImageField(upload_to='images')

class Video(ItemBase):
    url = models.URLField()

