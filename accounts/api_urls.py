from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    # Authentication endpoints
    path('register/', api_views.register_user, name='api_register'),
    path('login/', api_views.login_user, name='api_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile endpoints
    path('profile/', api_views.get_user_profile, name='api_profile'),
    path('profile/update/', api_views.update_user_profile, name='api_profile_update'),
    path('profile/change-password/', api_views.change_password, name='api_change_password'),
    
    # Admin endpoints
    path('riders/create/', api_views.create_rider, name='api_create_rider'),
    path('users/', api_views.list_users, name='api_list_users'),
]
