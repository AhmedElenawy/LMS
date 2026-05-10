import django_filters
from django.db.models import Case, When
from opensearchpy import Q

from .models import Course, Category
from .documents import CourseDocument

class CourseFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_opensearch_query')

    category = django_filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        method='filter_category_tree',
        conjoined=False
    )

    def filter_category_tree(self, queryset, name, value):
        if not value:
            return queryset
        
        # 'value' is a list of selected Category instances.
        # We loop through them and collect all of their descendant IDs.
        descendant_ids = set()
        for category in value:
            # get_descendants() is a built-in MPTT method
            ids = category.get_descendants(include_self=True).values_list('id', flat=True)
            descendant_ids.update(ids)
            
        # Filter courses that belong to any of these collected category IDs
        return queryset.filter(category__in=descendant_ids).distinct()
    
    # Added the OpenSearch processing method
    def filter_opensearch_query(self, queryset, name, value):
        if not value:
            return queryset
            
        q = Q(
            "multi_match",
              query=value,
             fields=['title^3', 'category.title^2',
                     'instructor_name^2',
                     'overview', 'prequirements'],
             fuzziness="AUTO")
        search_results = CourseDocument.search().query(q)
        
        course_ids = [hit.meta.id for hit in search_results[:200]]
        
        if not course_ids:
            return queryset.none() 
        
            
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(course_ids)])
        return queryset.filter(id__in=course_ids).order_by(preserved_order)


    class Meta:
        model = Course
        fields = ['min_price', 'max_price', 'category', 'instructor', 'search']