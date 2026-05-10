from django.contrib import admin

# Register your models here.
from .models import Category, Course, Module, Content, Text, Video, Image, File,Admin,Enrollment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug',]
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(Module)
admin.site.register(Content)
admin.site.register(Text)
admin.site.register(Video)
admin.site.register(Image)
admin.site.register(File)
admin.site.register(Admin)
admin.site.register(Enrollment)

