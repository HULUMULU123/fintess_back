import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()

User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'admin'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser "{username}" создан.')
else:
    print(f'Superuser "{username}" уже существует.')
