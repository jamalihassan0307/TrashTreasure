from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import TrashSubmission, CollectionRecord, RewardPointHistory, RewardClaim
from accounts.models import CustomUser
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator

def is_rider(user):
    return user.is_authenticated and user.user_type == 'rider'

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

@login_required
# Removed submit_trash view - now using modal with API

def track_submission(request, track_id):
    try:
        submission = TrashSubmission.objects.get(track_id=track_id)
        return render(request, 'trash/track_submission.html', {'submission': submission})
    except TrashSubmission.DoesNotExist:
        messages.error(request, 'Submission not found.')
        return redirect('dashboard:home')

@login_required
def submission_detail(request, submission_id):
    submission = get_object_or_404(TrashSubmission, id=submission_id)
    
    # Check if user has permission to view this submission
    if not (request.user == submission.user or 
            request.user.user_type in ['rider', 'admin'] or
            (request.user.user_type == 'rider' and submission.rider == request.user)):
        messages.error(request, 'You do not have permission to view this submission.')
        return redirect('dashboard:home')
    
    return render(request, 'trash/submission_detail.html', {'submission': submission})

@login_required
@user_passes_test(is_rider)
@require_http_methods(["POST"])
def update_status(request, submission_id):
    """Update the status of a trash submission"""
    try:
        # Parse JSON data
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return JsonResponse({'success': False, 'error': 'Status is required'})
        
        if new_status not in ['on_the_way', 'arrived', 'picked']:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
        
        submission = get_object_or_404(TrashSubmission, id=submission_id, rider=request.user)
        
        # Update submission status
        with transaction.atomic():
            submission.status = new_status
            if new_status == 'on_the_way':
                submission.assigned_at = timezone.now()
            elif new_status == 'picked':
                submission.pickup_time = timezone.now()
            
            if notes:
                submission.rider_notes = notes
            
            submission.save()
            
            # Log the action
            from accounts.models import ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action='updated_status',
                details={
                    'submission_id': submission.id,
                    'track_id': submission.track_id,
                    'old_status': submission.status,
                    'new_status': new_status,
                    'notes': notes
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Status updated to {new_status} successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_rider)
@require_http_methods(["POST"])
def complete_collection(request, submission_id):
    """Complete a trash collection"""
    try:
        submission = get_object_or_404(TrashSubmission, id=submission_id, rider=request.user)
        
        # Check if submission is in picked status
        if submission.status != 'picked':
            return JsonResponse({'success': False, 'error': 'Submission must be in picked status to complete'})
        
        # Get form data
        trash_type = request.POST.get('trash_type')
        actual_quantity = request.POST.get('actual_quantity')
        points_awarded = request.POST.get('points_awarded')
        # Removed collected_image handling
        rider_notes = request.POST.get('rider_notes', '')
        
        if not all([trash_type, actual_quantity, points_awarded]):
            return JsonResponse({'success': False, 'error': 'Please fill all required fields'})
        
        # Convert string values to appropriate types
        try:
            actual_quantity = float(actual_quantity) if actual_quantity else 0.0
            points_awarded = int(points_awarded) if points_awarded else 0
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid quantity or points format'})
        
        # Create collection record
        with transaction.atomic():
            collection = CollectionRecord.objects.create(
                submission=submission,
                rider=request.user,
                trash_type=trash_type,
                actual_quantity=actual_quantity,
                points_awarded=points_awarded
                # Removed collected_image field
            )
            
            # Update submission status
            submission.status = 'collected'
            submission.completion_time = timezone.now()
            submission.rider_notes = rider_notes
            submission.save()
            
            # Create reward point history
            from .models import RewardPointHistory
            RewardPointHistory.objects.create(
                user=submission.user,
                points=points_awarded,
                reason=f"Collected {actual_quantity}kg of {trash_type}",
                submission=submission,
                awarded_by=request.user
            )
            
            # Log the action
            from accounts.models import ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action='completed_collection',
                details={
                    'submission_id': submission.id,
                    'track_id': submission.track_id,
                    'trash_type': trash_type,
                    'actual_quantity': actual_quantity,
                    'points_awarded': points_awarded,
                    'notes': rider_notes
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Collection completed successfully! {points_awarded} points awarded.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
@require_http_methods(["POST"])
def assign_rider(request, submission_id):
    """Assign a rider to a trash submission"""
    try:
        # Parse JSON data
        data = json.loads(request.body)
        rider_id = data.get('rider')
        notes = data.get('notes', '')
        
        if not rider_id:
            return JsonResponse({'success': False, 'error': 'Rider ID is required'})
        
        # Get the submission and rider
        submission = get_object_or_404(TrashSubmission, id=submission_id)
        rider = get_object_or_404(CustomUser, id=rider_id, user_type='rider')
        
        # Check if submission is in pending status
        if submission.status != 'pending':
            return JsonResponse({'success': False, 'error': 'Submission is not in pending status'})
        
        # Update submission
        with transaction.atomic():
            submission.rider = rider
            submission.status = 'assigned'
            submission.assigned_at = timezone.now()
            submission.rider_notes = notes
            submission.save()
            
            # Log the action
            from accounts.models import ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action='assigned_rider',
                details={
                    'submission_id': submission.id,
                    'track_id': submission.track_id,
                    'rider_id': rider.id,
                    'rider_username': rider.username,
                    'notes': notes
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Rider {rider.username} assigned successfully to submission #{submission.track_id}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
@require_http_methods(["POST"])
def verify_collection(request, submission_id):
    """Verify a collection and award final points"""
    try:
        # Parse JSON data
        data = json.loads(request.body)
        points = data.get('points')
        notes = data.get('notes', '')
        admin_notes = data.get('admin_notes', '')
        
        if not points:
            return JsonResponse({'success': False, 'error': 'Points are required'})
        
        # Convert points to integer
        try:
            points = int(points)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid points format'})
        
        # Get the submission
        submission = get_object_or_404(TrashSubmission, id=submission_id)
        
        # Check if submission is collected
        if submission.status != 'collected':
            return JsonResponse({'success': False, 'error': 'Submission is not in collected status'})
        
        # Get or create collection record
        collection_record, created = CollectionRecord.objects.get_or_create(
            submission=submission,
            defaults={
                'rider': submission.rider,
                'trash_type': submission.trash_description or 'Mixed Waste',
                'actual_quantity': submission.quantity_kg or 0,
                'points_awarded': points,
                'admin_verified': True,
                'verified_by': request.user,
                'verified_at': timezone.now()
            }
        )
        
        if not created:
            # Update existing record
            collection_record.points_awarded = points
            collection_record.admin_verified = True
            collection_record.verified_by = request.user
            collection_record.verified_at = timezone.now()
            collection_record.save()
        
        # Update user's points
        user = submission.user
        user.reward_points += points
        user.save()
        
        # Change submission status to 'verified' to prevent re-verification
        submission.status = 'verified'
        submission.save()
        
        # Create reward point history entry
        from .models import RewardPointHistory
        RewardPointHistory.objects.create(
            user=user,
            points=points,
            reason=f'Collection verified by admin - {notes}' if notes else 'Collection verified by admin',
            submission=submission,
            awarded_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Collection verified successfully. {points} points awarded to {user.username}'
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@login_required
def claim_rewards(request):
    """View for the rewards claim page."""
    user = request.user
    user_claims = RewardClaim.objects.filter(user=user).order_by('-created_at')
    
    # Monetary conversion rate: 1 point = Rs. 10
    min_claim_amount = 500
    conversion_rate = 10
    monetary_amount = min_claim_amount * conversion_rate
    
    context = {
        'user': user,
        'available_points': user.reward_points,
        'min_claim_amount': min_claim_amount,
        'monetary_amount': monetary_amount,
        'conversion_rate': conversion_rate,
        'user_claims': user_claims
    }
    
    return render(request, 'trash/claim_rewards.html', context)


@login_required
@require_http_methods(["POST"])
def submit_claim(request):
    """Process a new reward claim submission."""
    user = request.user
    
    try:
        data = request.POST
        claim_amount = int(data.get('claim_amount', 0))
        claim_type = data.get('claim_type')
        
        # Validate claim amount and type
        if not claim_type or claim_type not in ['payment', 'donation']:
            messages.error(request, 'Please select a valid claim type.')
            return redirect('trash:claim_rewards')
            
        if claim_amount < 500:
            messages.error(request, 'Minimum claim amount is 500 points.')
            return redirect('trash:claim_rewards')
            
        if claim_amount > user.reward_points:
            messages.error(request, 'You cannot claim more points than you have available.')
            return redirect('trash:claim_rewards')
            
        # Get hospital if donation type
        donation_hospital = None
        if claim_type == 'donation':
            donation_hospital = data.get('donation_hospital')
            if not donation_hospital:
                messages.error(request, 'Please select a hospital for donation.')
                return redirect('trash:claim_rewards')
        
        # Validate claim amount
        if claim_amount < 500:
            messages.error(request, 'Minimum claim amount is 500 points.')
            return redirect('trash:claim_rewards')
        
        if claim_amount > user.reward_points:
            messages.error(request, 'You cannot claim more points than you have available.')
            return redirect('trash:claim_rewards')
        
        # Calculate monetary amount (Rs. 10 per point)
        monetary_amount = claim_amount * 10
        
        # Create the claim
        claim = RewardClaim.objects.create(
            user=user,
            claim_amount=claim_amount,
            monetary_amount=monetary_amount,
            claim_type=claim_type,
            donation_hospital=donation_hospital,
            status='pending'
        )
        
        messages.success(request, 
            f'Your claim for {claim_amount} points has been submitted successfully! ' 
            f'Reference ID: {claim.reference_id}'
        )
        
        return redirect('trash:claim_history')
        
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('trash:claim_rewards')


@login_required
def claim_history(request):
    """View for displaying user's claim history."""
    user = request.user
    
    # Get all claims for this user
    claims = RewardClaim.objects.filter(user=user).order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    per_page = int(request.GET.get('per_page', 10))
    
    if status_filter:
        claims = claims.filter(status=status_filter)
    
    if search_query:
        claims = claims.filter(
            Q(reference_id__icontains=search_query) |
            Q(claim_type__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(claims, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'claims': page_obj,
        'available_points': user.reward_points,
        'status_filter': status_filter,
        'search_query': search_query,
        'per_page': per_page,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    
    return render(request, 'trash/claim_history.html', context)


@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def manage_claims(request):
    """Admin view for managing reward claims."""
    claims = RewardClaim.objects.all().order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    claim_type_filter = request.GET.get('claim_type', '')
    search_query = request.GET.get('search', '')
    per_page = int(request.GET.get('per_page', 10))
    
    if status_filter:
        claims = claims.filter(status=status_filter)
    
    if claim_type_filter:
        claims = claims.filter(claim_type=claim_type_filter)
    
    if search_query:
        claims = claims.filter(
            Q(user__username__icontains=search_query) |
            Q(reference_id__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(donation_hospital__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(claims, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Status counts for summary
    status_counts = {
        'pending': RewardClaim.objects.filter(status='pending').count(),
        'processing': RewardClaim.objects.filter(status='processing').count(),
        'completed': RewardClaim.objects.filter(status='completed').count(),
        'cancelled': RewardClaim.objects.filter(status='cancelled').count(),
    }
    
    context = {
        'claims': page_obj,
        'status_filter': status_filter,
        'claim_type_filter': claim_type_filter,
        'search_query': search_query,
        'per_page': per_page,
        'status_counts': status_counts,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    
    return render(request, 'trash/manage_claims.html', context)
        

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
@require_http_methods(["POST"])
def update_claim_status(request, claim_id):
    """API endpoint to update claim status."""
    try:
        claim = RewardClaim.objects.get(id=claim_id)
        new_status = request.POST.get('status')
        
        if new_status not in ['processing', 'completed', 'cancelled']:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
        
        # Validate status transitions
        if new_status == 'completed' and claim.claim_amount < 500:
            return JsonResponse({'success': False, 'error': 'Claims below 500 points cannot be completed'})
        
        if new_status == 'completed' and claim.status != 'processing':
            return JsonResponse({'success': False, 'error': 'Only processing claims can be completed'})
        
        if new_status == 'completed' and claim.status == 'completed':
            return JsonResponse({'success': False, 'error': 'Claim is already completed'})
        
        # Update status
        claim.status = new_status
        claim.processed_by = request.user
        claim.processed_at = timezone.now()
        
        # Handle completed claims - deduct points when claim is completed
        if new_status == 'completed':
            # Deduct points from user when claim is completed
            user = claim.user
            user.reward_points -= claim.claim_amount
            user.save()
            
            # Log the point deduction
            RewardPointHistory.objects.create(
                user=user,
                points=-claim.claim_amount,  # Negative points for deduction
                reason=f"Claim {claim.reference_id} completed - points deducted",
                awarded_by=request.user
            )
        elif new_status == 'cancelled' and claim.status in ['pending', 'processing']:
            # Refund points if cancelling
            user = claim.user
            user.reward_points += claim.claim_amount
            user.save()
            
            RewardPointHistory.objects.create(
                user=user,
                points=claim.claim_amount,
                reason=f"Claim {claim.reference_id} cancelled - points refunded",
                awarded_by=request.user
            )
        
        claim.save()
        
        # Prepare success message
        if new_status == 'completed':
            message = f'Claim {claim.reference_id} completed successfully! {claim.claim_amount} points deducted from user.'
        else:
            message = f'Claim status updated to {new_status}'
        
        return JsonResponse({
            'success': True, 
            'message': message,
            'new_status': new_status
        })
        
    except RewardClaim.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Claim not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
        
