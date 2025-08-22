from django.urls import path
from . import api_views

urlpatterns = [
    # Public endpoints
    path('stats/public/', api_views.get_public_stats, name='api_public_stats'),
    
    # User dashboard
    path('stats/user/', api_views.get_user_dashboard_stats, name='api_user_dashboard_stats'),
    
    # Rider dashboard
    path('stats/rider/', api_views.get_rider_dashboard_stats, name='api_rider_dashboard_stats'),
    
    # Admin dashboard
    path('stats/admin/', api_views.get_admin_dashboard_stats, name='api_admin_dashboard_stats'),
    path('analytics/', api_views.get_admin_analytics, name='api_admin_analytics'),
    
    # System settings
    path('settings/', api_views.manage_system_settings, name='api_system_settings'),
    path('settings/reset/', api_views.reset_system_settings, name='api_reset_settings'),
    path('settings/clear-data/', api_views.clear_system_data, name='api_clear_data'),
]
