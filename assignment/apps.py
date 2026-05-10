from django.apps import AppConfig


class AssignmentConfig(AppConfig):
    name = 'assignment'

    def ready(self):
        import assignment.signals
