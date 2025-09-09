from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.conf import settings as django_settings
from django.template.loader import render_to_string

class SystemStatusMiddleware:
    """Middleware to check system status and redirect users accordingly"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Handle 404 redirects to accounts/login/ - redirect to correct login URL
        if request.path.startswith('/accounts/login/'):
            return redirect('dashboard:login')
        
        # Skip middleware for admin users and certain paths
        if self._should_skip_middleware(request):
            return self.get_response(request)
        
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
                        return redirect('dashboard:maintenance')
            
            # Check debug mode
            if system_settings.debug_mode:
                if not self._is_admin_user(request):
                    # If user is not admin and debug mode is on, show under construction page
                    # But only if they're not already trying to access it
                    if request.path != '/under-construction/':
                        return redirect('dashboard:under_construction')
                    
        except Exception as e:
            # If there's an error getting settings, continue normally
            # You can log this error if needed
            pass
        
        # Get the response
        response = self.get_response(request)
        
        # Handle 404 errors with custom page
        if response.status_code == 404:
            return self._handle_404(request)
        
        return response
    
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
        
        # Skip for API endpoints
        if request.path.startswith('/api/'):
            return True
        
        return False
    
    def _is_admin_user(self, request):
        """Check if the current user is an admin"""
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'user_type') and 
                request.user.user_type == 'admin')
    
    def _handle_404(self, request):
        """Handle 404 errors with a custom page"""
        try:
            # Render custom 404 page
            html = render_to_string('dashboard/404.html', {
                'request_path': request.path,
                'user': request.user,
            })
            return HttpResponse(html, status=404)
        except:
            # Fallback to simple 404 response
            return HttpResponse(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Page Not Found - Trash to Treasure</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                        .error-container {{ max-width: 600px; margin: 0 auto; }}
                        .error-code {{ font-size: 72px; color: #e74c3c; margin: 0; }}
                        .error-message {{ font-size: 24px; color: #333; margin: 20px 0; }}
                        .error-description {{ font-size: 16px; color: #666; margin: 20px 0; }}
                        .btn {{ display: inline-block; padding: 12px 24px; background: #2e7d32; color: white; text-decoration: none; border-radius: 5px; margin: 20px 10px; }}
                        .btn:hover {{ background: #1b5e20; }}
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h1 class="error-code">404</h1>
                        <h2 class="error-message">Page Not Found</h2>
                        <p class="error-description">
                            The page you're looking for doesn't exist or has been moved.
                        </p>
                        <p class="error-description">
                            Requested path: <code>{request.path}</code>
                        </p>
                        <a href="/" class="btn">Go Home</a>
                        <a href="/login/" class="btn">Login</a>
                    </div>
                </body>
                </html>
                """, 
                status=404
            )
