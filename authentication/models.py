from django.db import models
from django.conf import settings


class Student(models.Model):
    class RelatedObjects(models.Manager):
        def get_queryset(self):
            return super().get_queryset().select_related('user')
            
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_info')
    date_of_birth = models.DateField(blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)

    objects = models.Manager()
    related_objects = RelatedObjects()

    def __str__(self):
        # Fallback to username if get_full_name() returns an empty string
        return self.user.get_full_name() or self.user.username


class Instructor(models.Model):
    class RelatedObjects(models.Manager):
        def get_queryset(self):
            return super().get_queryset().select_related('user')

    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="instructor_info")
    bio = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='instructor_images', null=True, blank=True)

    objects = models.Manager()
    related_objects = RelatedObjects()

    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return f"Instructor (ID: {self.id})"
