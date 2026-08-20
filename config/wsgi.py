import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

import os
from django.core.wsgi import get_wsgi_application


from django.contrib.auth import get_user_model
try:
    User = get_user_model()
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(username="admin", email="admin@gmail.com", password="password123")
        print("Superuser automatically created!")
except Exception as e:
    print(f"Skipped superuser creation: {e}")

application = get_wsgi_application()
