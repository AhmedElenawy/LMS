from django.contrib import admin

from .models import *

admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(Question)
admin.site.register(MCQAnswer)      