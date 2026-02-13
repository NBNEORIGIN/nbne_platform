#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'toby@nbnesigns.com', '!49Monkswood')
    print("Superuser 'admin' created successfully!")
else:
    print("Superuser 'admin' already exists.")
