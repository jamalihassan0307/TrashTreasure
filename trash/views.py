from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import TrashSubmission, CollectionRecord
from accounts.models import CustomUser
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_http_methods
from django.db import transaction

def is_rider(user):
    return user.is_authenticated and user.user_type == 'rider'

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

@login_required
def submit_trash(request):
    if request.method == 'POST':
        trash_description = request.POST.get('trash_description')
        quantity_kg = request.POST.get('quantity_kg')
        location = request.POST.get('location')
        # Removed image handling
        
        if not all([trash_description, location]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'trash/submit_trash.html')
        
        # Convert quantity_kg to float if provided
        try:
            quantity_kg = float(quantity_kg) if quantity_kg else None
        except (ValueError, TypeError):
            quantity_kg = None
        
        submission = TrashSubmission.objects.create(
            user=request.user,
            trash_description=trash_description,
            quantity_kg=quantity_kg,
            location=location
            # Removed image field
        )
        
        messages.success(request, f'Trash submission created successfully! Track ID: {submission.track_id}')
        return redirect('trash:submission_detail', submission_id=submission.id)
    
    return render(request, 'trash/submit_trash.html')

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
