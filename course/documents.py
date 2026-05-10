from django_opensearch_dsl import Document, fields
from django_opensearch_dsl.registries import registry
from .models import Course, Category
from authentication.models import Instructor

@registry.register_document
class CourseDocument(Document):
    # indirect gonna use prepare
    instructor_name = fields.TextField()
    # direct relation
    category = fields.ObjectField(properties={
        'title': fields.TextField(),
    })
    class Index:
        name = 'courses'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = Course
        
        # We are ONLY indexing the direct fields on the Course itself.
        # No complex relationships, no extra signal handlers needed!
        fields = [
            'title', 
            'slug',
            'overview',
            'features',
            'prequirements',
        ]
    def prepare_instructor_name(self, instance):
        if instance.instructor and instance.instructor.user:
            return instance.instructor.user.get_full_name()
        return ""
    # when a signal of category or instructor is fired, tell search which courses related to be apdated
    
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Category):
            return related_instance.category_courses.all() 
        elif isinstance(related_instance, Instructor):
            return related_instance.instructor_courses.all()




