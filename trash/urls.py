from django.urls import path
from . import views

app_name = 'trash'

urlpatterns = [
    # Removed submit_trash page - now using modal
    path('track/<str:track_id>/', views.track_submission, name='track_submission'),
    path('submission/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('update-status/<int:submission_id>/', views.update_status, name='update_status'),
    path('complete-collection/<int:submission_id>/', views.complete_collection, name='complete_collection'),
    path('assign-rider/<int:submission_id>/', views.assign_rider, name='assign_rider'),
    path('verify-collection/<int:submission_id>/', views.verify_collection, name='verify_collection'),
    
    # Reward Claim URLs
    path('claim-rewards/', views.claim_rewards, name='claim_rewards'),
    path('submit-claim/', views.submit_claim, name='submit_claim'),
    path('claim-history/', views.claim_history, name='claim_history'),
    path('manage-claims/', views.manage_claims, name='manage_claims'),
    path('update-claim-status/<int:claim_id>/', views.update_claim_status, name='update_claim_status'),
    path('delete-claim/<int:claim_id>/', views.delete_claim, name='delete_claim'),
]
