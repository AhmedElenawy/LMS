from django.contrib.auth.models import User

# when call authenticate it will eterate over this after check with username
class EmailAuthBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email') or username
        if not email:
            return None
        try:
            user = User.objects.get(email=email)
            if user.check_password(password) and user.is_active:
                return user
            return None
        except (User.DoesNotExist, User.MultipleObjectsReturned):    
            return None
        
    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None

