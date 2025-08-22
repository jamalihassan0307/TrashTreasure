from django.urls import path
from . import api_views

urlpatterns = [
    # Submission endpoints
    path('submit/', api_views.submit_trash, name='api_submit_trash'),
    path('submissions/', api_views.get_user_submissions, name='api_user_submissions'),
    path('track/<str:track_id>/', api_views.track_submission, name='api_track_submission'),
    path('submissions/<int:submission_id>/', api_views.submission_detail, name='api_submission_detail'),
    
    # Rider endpoints
    path('submissions/<int:submission_id>/update-status/', api_views.update_submission_status, name='api_update_status'),
    path('submissions/<int:submission_id>/complete/', api_views.complete_collection, name='api_complete_collection'),
    path('rider/collections/', api_views.rider_collections, name='api_rider_collections'),
    
    # Admin endpoints
    path('submissions/<int:submission_id>/assign/', api_views.assign_rider, name='api_assign_rider'),
    path('submissions/<int:submission_id>/verify/', api_views.verify_collection, name='api_verify_collection'),
    
    # Points history
    path('points/history/', api_views.user_points_history, name='api_points_history'),
]
