#!/usr/bin/env python
"""
Create new client instance from Django template
Usage: python scripts/create_instance.py <client_name> <instance_path>
"""

import os
import sys
import shutil
import secrets
import subprocess
from pathlib import Path

def generate_secret_key():
    """Generate Django SECRET_KEY"""
    return secrets.token_urlsafe(50)

def generate_password(length=25):
    """Generate random password"""
    return secrets.token_urlsafe(length)[:length]

def create_instance(client_name, instance_path):
    """Create new client instance"""
    
    print(f"🚀 Creating new instance: {client_name}")
    print(f"📁 Instance path: {instance_path}")
    print()
    
    template_dir = Path.cwd()
    instance_dir = Path(instance_path)
    
    # Validate template directory
    if not (template_dir / 'manage.py').exists():
        print("❌ Error: Must run from Django project root")
        sys.exit(1)
    
    # Check if instance exists
    if instance_dir.exists():
        confirm = input(f"⚠️  Instance directory exists. Overwrite? (yes/no): ")
        if confirm != 'yes':
            print("❌ Cancelled")
            sys.exit(0)
        shutil.rmtree(instance_dir)
    
    # Create instance directory
    print("📦 Copying template files...")
    instance_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy files excluding specific directories
    exclude_dirs = {'venv', '__pycache__', '.git', 'backups', 'staticfiles'}
    exclude_files = {'.env', 'db.sqlite3'}
    
    for item in template_dir.iterdir():
        if item.name in exclude_dirs or item.name in exclude_files:
            continue
        
        dest = instance_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        else:
            shutil.copy2(item, dest)
    
    # Generate credentials
    db_password = generate_password()
    secret_key = generate_secret_key()
    
    # Create instance .env
    print("⚙️  Configuring environment...")
    env_content = f"""# Database
DB_NAME={client_name}_db
DB_USER={client_name}_user
DB_PASSWORD={db_password}
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY={secret_key}
DEBUG=False
ALLOWED_HOSTS={client_name}.com,www.{client_name}.com,localhost

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_FROM=noreply@{client_name}.com

# Feature Flags
ENABLE_SMS=False
ENABLE_WAITLIST=True
ENABLE_PORTAL=True

# Branding
CLIENT_NAME={client_name.replace('-', ' ').replace('_', ' ').title()}
PRIMARY_COLOR=#3B82F6
SECONDARY_COLOR=#10B981
"""
    
    (instance_dir / '.env').write_text(env_content)
    
    # Create backups directory
    (instance_dir / 'backups').mkdir(exist_ok=True)
    
    print()
    print("✅ Instance created successfully!")
    print()
    print("📋 Instance Details:")
    print(f"  Name: {client_name}")
    print(f"  Path: {instance_path}")
    print(f"  Database: {client_name}_db")
    print(f"  Database User: {client_name}_user")
    print()
    print("🔐 Credentials saved to: {instance_path}\\.env")
    print()
    print("Next steps:")
    print(f"1. cd {instance_path}")
    print(f"2. Create PostgreSQL database and user:")
    print(f"   CREATE DATABASE {client_name}_db;")
    print(f"   CREATE USER {client_name}_user WITH PASSWORD '{db_password}';")
    print(f"   GRANT ALL PRIVILEGES ON DATABASE {client_name}_db TO {client_name}_user;")
    print("3. python manage.py migrate")
    print("4. python manage.py seed_config")
    print("5. python manage.py createsuperuser")
    print("6. python manage.py runserver")
    print()
    print("For production deployment:")
    print("7. python manage.py collectstatic")
    print("8. Configure IIS/Waitress/Gunicorn")
    print("9. Set up automated backups")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_instance.py <client_name> <instance_path>")
        print("Example: python scripts/create_instance.py house-of-hair D:\\clients\\house-of-hair")
        sys.exit(1)
    
    client_name = sys.argv[1]
    instance_path = sys.argv[2]
    
    create_instance(client_name, instance_path)
