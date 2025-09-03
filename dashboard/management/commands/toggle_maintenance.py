from django.core.management.base import BaseCommand
from dashboard.models import SystemSettings

class Command(BaseCommand):
    help = 'Toggle maintenance mode on/off'

    def add_arguments(self, parser):
        parser.add_argument(
            '--on',
            action='store_true',
            help='Turn maintenance mode ON',
        )
        parser.add_argument(
            '--off',
            action='store_true',
            help='Turn maintenance mode OFF',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current maintenance status',
        )

    def handle(self, *args, **options):
        settings = SystemSettings.get_settings()
        
        if options['status']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Maintenance Mode: {"ON" if settings.maintenance_mode else "OFF"}'
                )
            )
            self.stdout.write(
                f'Debug Mode: {"ON" if settings.debug_mode else "OFF"}'
            )
            self.stdout.write(f'Log Level: {settings.log_level}')
            return
        
        if options['on']:
            settings.maintenance_mode = True
            settings.save()
            self.stdout.write(
                self.style.SUCCESS('Maintenance mode turned ON')
            )
        elif options['off']:
            settings.maintenance_mode = False
            settings.save()
            self.stdout.write(
                self.style.SUCCESS('Maintenance mode turned OFF')
            )
        else:
            # Toggle current state
            settings.maintenance_mode = not settings.maintenance_mode
            settings.save()
            status = "ON" if settings.maintenance_mode else "OFF"
            self.stdout.write(
                self.style.SUCCESS(f'Maintenance mode toggled to {status}')
            )
