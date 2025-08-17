from django.db import models
from django.utils import timezone

# Create your models here.

class SystemSettings(models.Model):
    """System-wide settings and configuration"""
    
    # General Settings
    site_name = models.CharField(max_length=100, default='Trash to Treasure')
    site_description = models.TextField(default='Transform waste into rewards with our eco-friendly recycling platform')
    contact_email = models.EmailField(default='admin@trashtotreasure.com')
    default_timezone = models.CharField(max_length=50, default='UTC')
    
    # System Maintenance
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(default='System is currently under maintenance. Please check back later.')
    debug_mode = models.BooleanField(default=False)
    log_level = models.CharField(max_length=20, choices=[
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('DEBUG', 'Debug'),
    ], default='INFO')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return f"System Settings - {self.site_name}"
    
    @classmethod
    def get_settings(cls):
        """Get or create system settings singleton"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'site_name': 'Trash to Treasure',
                'site_description': 'Transform waste into rewards with our eco-friendly recycling platform',
                'contact_email': 'admin@trashtotreasure.com',
                'default_timezone': 'UTC',
                'maintenance_mode': False,
                'maintenance_message': 'System is currently under maintenance. Please check back later.',
                'debug_mode': False,
                'log_level': 'INFO',
            }
        )
        return settings
    
    @classmethod
    def reset_to_defaults(cls):
        """Reset all settings to default values"""
        settings = cls.get_settings()
        settings.site_name = 'Trash to Treasure'
        settings.site_description = 'Transform waste into rewards with our eco-friendly recycling platform'
        settings.contact_email = 'admin@trashtotreasure.com'
        settings.default_timezone = 'UTC'
        settings.maintenance_mode = False
        settings.maintenance_message = 'System is currently under maintenance. Please check back later.'
        settings.debug_mode = False
        settings.log_level = 'INFO'
        settings.save()
        return settings
