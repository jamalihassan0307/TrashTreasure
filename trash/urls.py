from django.urls import path
from . import views

app_name = 'trash'

urlpatterns = [
    path('submit/', views.submit_trash, name='submit_trash'),
    path('track/<str:track_id>/', views.track_submission, name='track_submission'),
    path('submission/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('update-status/<int:submission_id>/', views.update_status, name='update_status'),
    path('complete-collection/<int:submission_id>/', views.complete_collection, name='complete_collection'),
    path('assign-rider/<int:submission_id>/', views.assign_rider, name='assign_rider'),
    path('verify-collection/<int:submission_id>/', views.verify_collection, name='verify_collection'),
]
