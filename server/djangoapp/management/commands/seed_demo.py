"""Seed a repeatable car catalog and local demonstration users."""
import json
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from djangoapp.models import CarMake, CarModel


class Command(BaseCommand):
    def handle(self, *args, **options):
        data = json.loads((Path(__file__).resolve().parents[3] / 'database/data/car_records.json').read_text())
        for car in data['cars']:
            make, _ = CarMake.objects.get_or_create(name=car['make'], defaults={'description': f"{car['make']} passenger vehicles"})
            CarModel.objects.get_or_create(car_make=make, name=car['model'], year=car['year'], defaults={'type': car['bodyType']})
        for username, variable, admin in [('root', 'DEMO_ADMIN_PASSWORD', True), ('demo_user', 'DEMO_USER_PASSWORD', False)]:
            password = os.environ.get(variable)
            if password:
                user, created = User.objects.get_or_create(username=username, defaults={'first_name': 'Demo', 'last_name': 'Customer'})
                if created:
                    user.set_password(password)
                    user.is_staff = user.is_superuser = admin
                    user.save()
        self.stdout.write(self.style.SUCCESS('Car catalog and configured demo users are ready.'))
