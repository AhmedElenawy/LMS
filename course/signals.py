from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Category

# Define your cache key exactly as it is written in your views/services
CATEGORY_TREE_CACHE_KEY = 'category_tree' 

# Pass a list of signals to the decorator to listen for both save and delete
@receiver([post_save, post_delete], sender=Category)
def clear_category_tree_cache(sender, instance, **kwargs):
    """
    This function runs whenever a Category is created, updated, or deleted.
    It deletes the cached category tree so the next request fetches fresh data.
    """
    cache.delete(CATEGORY_TREE_CACHE_KEY)
    print(f"Cache key '{CATEGORY_TREE_CACHE_KEY}' has been cleared because Category '{instance.title}' changed.")