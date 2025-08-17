from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('rider-dashboard/', views.rider_dashboard, name='rider_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('create-rider/', views.create_rider, name='create_rider'),
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    
    # New User Dashboard Pages
    path('user-submissions/', views.user_submissions, name='user_submissions'),
    path('user-points/', views.user_points, name='user_points'),
    
    # New Rider Dashboard Pages
    path('rider-earnings/', views.rider_earnings, name='rider_earnings'),
    
    # New Admin Dashboard Pages
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin-settings/', views.admin_settings, name='admin_settings'),
    
    # System Status Pages
    path('maintenance/', views.maintenance_page, name='maintenance_page'),
    path('under-construction/', views.under_construction_page, name='under_construction_page'),
]
