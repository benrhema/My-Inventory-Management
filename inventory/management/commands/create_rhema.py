from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create Rhema superuser'

    def handle(self, *args, **options):
        if User.objects.filter(username='Rhema').exists():
            self.stdout.write(self.style.SUCCESS('Rhema already exists'))
            return

        user = User.objects.create_superuser(
            username='Rhema',
            password='2504@2005ben2'
        )
        self.stdout.write(self.style.SUCCESS('Rhema superuser created!'))

