from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alerts'
    
    def ready(self):
        import threading
        from .views import corun
        thread = threading.Thread(target=corun)
        thread.start()

