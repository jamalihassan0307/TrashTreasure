from django.urls import path, include

# Main API URLs configuration
api_urlpatterns = [
    # Include app-specific API URLs
    path('accounts/', include('accounts.api_urls')),
    path('dashboard/', include('dashboard.api_urls')),
    path('trash/', include('trash.api_urls')),
]

# API documentation and health check endpoints
urlpatterns = [
    path('api/', include(api_urlpatterns)),
    path('api/health/', include([
        path('', lambda request: {'status': 'healthy'}, name='api_health'),
    ])),
]
