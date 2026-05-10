from django.contrib.contenttypes.models import ContentType
# Assuming your app with the Content model is named 'course' or 'education'
from course.models import Content 

# 1. Find the old ContentType (app_label='course', model='assignment')
old_ct = ContentType.objects.filter(app_label='course', model='assignment').first()

# 2. Find the new ContentType (app_label='assignment', model='assignment')
# Django usually creates this automatically when you run migrations for the new app
new_ct = ContentType.objects.filter(app_label='assignment', model='assignment').first()

if old_ct and new_ct:
    # 3. Find all course contents still pointing to the old app
    orphaned_contents = Content.objects.filter(content_type=old_ct)
    count = orphaned_contents.count()
    
    # 4. Update them to point to the new app
    orphaned_contents.update(content_type=new_ct)
    print(f"Successfully updated {count} Content objects to the new Assignment ContentType.")
    
    # 5. Clean up the old, stale ContentType so it doesn't cause future errors
    old_ct.delete()
    print("Deleted the old course.assignment ContentType.")
    
elif not new_ct:
    print("Could not find the new ContentType. Did you run `python manage.py migrate` after creating the new assignment app?")
else:
    print("Old ContentType not found. It might have already been deleted or updated.")