from django.core.management.base import BaseCommand
from dashboard.models import SystemSettings

class Command(BaseCommand):
    help = 'Toggle debug mode on/off'

    def add_arguments(self, parser):
        parser.add_argument(
            '--on',
            action='store_true',
            help='Turn debug mode ON',
        )
        parser.add_argument(
            '--off',
            action='store_true',
            help='Turn debug mode OFF',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current debug status',
        )

    def handle(self, *args, **options):
        settings = SystemSettings.get_settings()
        
        if options['status']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Debug Mode: {"ON" if settings.debug_mode else "OFF"}'
                )
            )
            self.stdout.write(
                f'Maintenance Mode: {"ON" if settings.maintenance_mode else "OFF"}'
            )
            self.stdout.write(f'Log Level: {settings.log_level}')
            return
        
        if options['on']:
            settings.debug_mode = True
            settings.save()
            self.stdout.write(
                self.style.SUCCESS('Debug mode turned ON')
            )
        elif options['off']:
            settings.debug_mode = False
            settings.save()
            self.stdout.write(
                self.style.SUCCESS('Debug mode turned OFF')
            )
        else:
            # Toggle current state
            settings.debug_mode = not settings.debug_mode
            settings.save()
            status = "ON" if settings.debug_mode else "OFF"
            self.stdout.write(
                self.style.SUCCESS(f'Debug mode toggled to {status}')
            )
