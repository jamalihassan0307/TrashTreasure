from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings as django_settings

class SystemStatusMiddleware:
    """Middleware to check system status and redirect users accordingly"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip middleware for admin users and certain paths
       
        
        # Check system settings
        try:
            from .models import SystemSettings
            system_settings = SystemSettings.get_settings()
            
            # Check maintenance mode
            if system_settings.maintenance_mode:
                if not self._is_admin_user(request):
                    # If user is not admin and maintenance mode is on, show maintenance page
                    # But only if they're not already trying to access it
                    if request.path != '/maintenance/':
                        return redirect('dashboard:maintenance_page')
            
            # Check debug mode
            if system_settings.debug_mode:
                if not self._is_admin_user(request):
                    # If user is not admin and debug mode is on, show under construction page
                    # But only if they're not already trying to access it
                    if request.path != '/under-construction/':
                        return redirect('dashboard:under_construction_page')
                    
        except Exception:
            # If there's an error getting settings, continue normally
            pass
        
        return self.get_response(request)
    
    def _should_skip_middleware(self, request):
        """Check if middleware should be skipped for this request"""
        # Skip for admin users
        if self._is_admin_user(request):
            return True
        
        # Skip for static and media files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return True
        
        # Skip for maintenance and construction pages themselves
        if request.path in ['/maintenance/', '/under-construction/']:
            return True
        
        # Skip for login and logout
        if request.path in ['/login/', '/logout/']:
            return True
        
        # Skip for Django admin panel
        if request.path.startswith('/admin/'):
            return True
        
        # Skip for register page
        if request.path == '/register/':
            return True
        
        return False
    
    def _is_admin_user(self, request):
        """Check if the current user is an admin"""
        return (request.user.is_authenticated and 
                hasattr(request.user, 'user_type') and 
                request.user.user_type == 'admin')
