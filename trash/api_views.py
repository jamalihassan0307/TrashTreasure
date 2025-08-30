from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator

from .models import TrashSubmission, CollectionRecord, RewardPointHistory, RewardClaim
from .serializers import (
    TrashSubmissionSerializer, 
    TrashSubmissionCreateSerializer,
    CollectionRecordSerializer,
    CollectionRecordCreateSerializer,
    RewardPointHistorySerializer,
    RewardClaimSerializer,
    RewardClaimCreateSerializer,
    RewardClaimUpdateSerializer,
    TrashSubmissionStatusUpdateSerializer,
    RiderAssignmentSerializer,
    CollectionVerificationSerializer
)
from accounts.utils import token_required, get_user_id_by_token

@api_view(['POST'])
@token_required()
def submit_trash(request):
    """Submit new trash collection request"""
    serializer = TrashSubmissionCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                submission = serializer.save(user=request.user)
                full_serializer = TrashSubmissionSerializer(submission)
                return Response({
                    'success': True,
                    'message': f'Trash submission created successfully! Track ID: {submission.track_id}',
                    'submission': full_serializer.data
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({
        'success': False,
        'error': 'Invalid data',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@token_required()
def get_user_submissions(request):
    """Get all submissions for the current user with filtering and pagination"""
    # Apply filters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    submissions = TrashSubmission.objects.filter(user=request.user).order_by('-created_at')
    
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            submissions = submissions.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timezone.timedelta(days=7)
            submissions = submissions.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timezone.timedelta(days=30)
            submissions = submissions.filter(created_at__date__gte=month_ago)
    
    if search_query:
        submissions = submissions.filter(
            Q(location__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(submissions, 12)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    serializer = TrashSubmissionSerializer(page_obj, many=True)
    
    return Response({
        'success': True,
        'submissions': serializer.data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })

@api_view(['GET'])
def track_submission(request, track_id):
    """Track submission by track ID (public endpoint)"""
    try:
        submission = TrashSubmission.objects.get(track_id=track_id)
        serializer = TrashSubmissionSerializer(submission)
        return Response({
            'success': True,
            'submission': serializer.data
        })
    except TrashSubmission.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Submission not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@token_required()
def submission_detail(request, submission_id):
    """Get detailed submission info"""
    try:
        submission = TrashSubmission.objects.get(id=submission_id)
        
        # Check permission
        if not (request.user == submission.user or 
                request.user.user_type in ['rider', 'admin'] or
                (request.user.user_type == 'rider' and submission.rider == request.user)):
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TrashSubmissionSerializer(submission)
        return Response({
            'success': True,
            'submission': serializer.data
        })
        
    except TrashSubmission.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Submission not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required(['rider'])
def update_submission_status(request, submission_id):
    """Update submission status (rider only)"""
    serializer = TrashSubmissionStatusUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        submission = TrashSubmission.objects.get(id=submission_id, rider=request.user)
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        if new_status not in ['on_the_way', 'arrived', 'picked']:
            return Response({
                'success': False,
                'error': 'Invalid status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            submission.status = new_status
            if new_status == 'on_the_way':
                submission.assigned_at = timezone.now()
            elif new_status == 'picked':
                submission.pickup_time = timezone.now()
            
            if notes:
                submission.rider_notes = notes
            
            submission.save()
        
        result_serializer = TrashSubmissionSerializer(submission)
        return Response({
            'success': True,
            'message': f'Status updated to {new_status} successfully',
            'submission': result_serializer.data
        })
        
    except TrashSubmission.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Submission not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required(['rider'])
def complete_collection(request, submission_id):
    """Complete a trash collection (rider only)"""
    serializer = CollectionRecordCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        submission = TrashSubmission.objects.get(id=submission_id, rider=request.user)
        
        if submission.status != 'picked':
            return Response({
                'success': False,
                'error': 'Submission must be in picked status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            collection = CollectionRecord.objects.create(
                submission=submission,
                rider=request.user,
                trash_type=serializer.validated_data['trash_type'],
                actual_quantity=serializer.validated_data['actual_quantity'],
                points_awarded=serializer.validated_data['points_awarded']
            )
            
            # Update submission status
            submission.status = 'collected'
            submission.completion_time = timezone.now()
            submission.save()
            
            # Create reward point history
            RewardPointHistory.objects.create(
                user=submission.user,
                points=collection.points_awarded,
                reason=f"Collected {collection.actual_quantity}kg of {collection.trash_type}",
                submission=submission,
                awarded_by=request.user
            )
        
        result_serializer = CollectionRecordSerializer(collection)
        return Response({
            'success': True,
            'message': f'Collection completed successfully! {collection.points_awarded} points awarded.',
            'collection': result_serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except TrashSubmission.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Submission not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required(['admin'])
def assign_rider(request, submission_id):
    """Assign rider to submission (admin only)"""
    serializer = RiderAssignmentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        submission = TrashSubmission.objects.get(id=submission_id)
        rider_id = serializer.validated_data['rider']
        notes = serializer.validated_data.get('notes', '')
        
        if submission.status != 'pending':
            return Response({
                'success': False,
                'error': 'Submission is not in pending status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from accounts.models import CustomUser
        rider = CustomUser.objects.filter(id=rider_id, user_type='rider').first()
        if not rider:
            return Response({
                'success': False,
                'error': 'Invalid rider'
            }, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            submission.rider = rider
            submission.status = 'assigned'
            submission.assigned_at = timezone.now()
            submission.rider_notes = notes
            submission.save()
        
        result_serializer = TrashSubmissionSerializer(submission)
        return Response({
            'success': True,
            'message': f'Rider {rider.username} assigned successfully to submission #{submission.track_id}',
            'submission': result_serializer.data
        })
        
    except TrashSubmission.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Submission not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required(['admin'])
def verify_collection(request, submission_id):
    """Verify collection and award points (admin only)"""
    serializer = CollectionVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        submission = TrashSubmission.objects.get(id=submission_id)
        points = serializer.validated_data['points']
        notes = serializer.validated_data.get('notes', '')
        admin_notes = serializer.validated_data.get('admin_notes', '')
        
        if submission.status != 'collected':
            return Response({
                'success': False,
                'error': 'Submission is not in collected status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Get or create collection record
            collection_record, created = CollectionRecord.objects.get_or_create(
                submission=submission,
                defaults={
                    'rider': submission.rider,
                    'trash_type': 'Mixed Waste',
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
            
            # Change submission status to 'verified'
            submission.status = 'verified'
            submission.save()
            
            # Create reward point history entry
            RewardPointHistory.objects.create(
                user=user,
                points=points,
                reason=f'Collection verified by admin - {notes}' if notes else 'Collection verified by admin',
                submission=submission,
                awarded_by=request.user
            )
            
        result_serializer = CollectionRecordSerializer(collection_record)
        return Response({
            'success': True,
            'message': f'Collection verified successfully. {points} points awarded to {user.username}',
            'collection': result_serializer.data
        })
        
    except TrashSubmission.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Submission not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@token_required(['rider'])
def rider_collections(request):
    """Get rider's collection history with filtering and pagination"""
    collections = CollectionRecord.objects.filter(rider=request.user).order_by('-collected_at')
    
    # Apply filters
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            collections = collections.filter(collected_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timezone.timedelta(days=7)
            collections = collections.filter(collected_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timezone.timedelta(days=30)
            collections = collections.filter(collected_at__date__gte=month_ago)
    
    if search_query:
        collections = collections.filter(
            Q(submission__location__icontains=search_query) |
            Q(trash_type__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(collections, 20)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    serializer = CollectionRecordSerializer(page_obj, many=True)
    
    return Response({
        'success': True,
        'collections': serializer.data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })

@api_view(['GET'])
@token_required()
def user_points_history(request):
    """Get user's point history with filtering and pagination"""
    history = RewardPointHistory.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    type_filter = request.GET.get('type', '')
    date_filter = request.GET.get('date', '')
    page = request.GET.get('page', 1)
    
    if type_filter:
        if type_filter == 'earned':
            history = history.filter(points__gt=0)
        elif type_filter == 'spent':
            history = history.filter(points__lt=0)
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            history = history.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timezone.timedelta(days=7)
            history = history.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timezone.timedelta(days=30)
            history = history.filter(created_at__date__gte=month_ago)
    
    # Pagination
    paginator = Paginator(history, 20)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    serializer = RewardPointHistorySerializer(page_obj, many=True)
    
    return Response({
        'success': True,
        'history': serializer.data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })

# Reward Claim API Views
@api_view(['GET'])
@token_required()
def get_claim_rewards_info(request):
    """Get information for the rewards claim page"""
    user = request.user
    user_claims = RewardClaim.objects.filter(user=user).order_by('-created_at')
    
    # Monetary conversion rate: 1 point = Rs. 10
    min_claim_amount = 500
    conversion_rate = 10
    monetary_amount = min_claim_amount * conversion_rate
    
    return Response({
        'success': True,
        'available_points': user.reward_points,
        'min_claim_amount': min_claim_amount,
        'monetary_amount': monetary_amount,
        'conversion_rate': conversion_rate,
        'recent_claims': RewardClaimSerializer(user_claims[:5], many=True).data
    })

@api_view(['POST'])
@token_required()
def submit_claim(request):
    """Process a new reward claim submission"""
    serializer = RewardClaimCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    claim_amount = serializer.validated_data['claim_amount']
    claim_type = serializer.validated_data['claim_type']
    donation_hospital = serializer.validated_data.get('donation_hospital', '')
    
    # Validate claim amount
    if claim_amount < 500:
        return Response({
            'success': False,
            'error': 'Minimum claim amount is 500 points'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    if claim_amount > user.reward_points:
        return Response({
            'success': False,
            'error': 'You cannot claim more points than you have available'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    # Get hospital if donation type
    if claim_type == 'donation' and not donation_hospital:
        return Response({
            'success': False,
            'error': 'Please select a hospital for donation'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create the claim
            claim = RewardClaim.objects.create(
                user=user,
                claim_amount=claim_amount,
                claim_type=claim_type,
                donation_hospital=donation_hospital,
                status='pending'
            )
            
            result_serializer = RewardClaimSerializer(claim)
            return Response({
                'success': True,
                'message': f'Your claim for {claim_amount} points has been submitted successfully! Reference ID: {claim.reference_id}',
                'claim': result_serializer.data
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@token_required()
def get_claim_history(request):
    """Get user's claim history with filtering and pagination"""
    user = request.user
    claims = RewardClaim.objects.filter(user=user).order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    if status_filter:
        claims = claims.filter(status=status_filter)
    
    if search_query:
        claims = claims.filter(
            Q(reference_id__icontains=search_query) |
            Q(claim_type__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(claims, 10)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    serializer = RewardClaimSerializer(page_obj, many=True)
    
    return Response({
        'success': True,
        'claims': serializer.data,
        'available_points': user.reward_points,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })

@api_view(['GET'])
@token_required(['admin'])
def get_manage_claims(request):
    """Admin view for managing reward claims with filtering and pagination"""
    claims = RewardClaim.objects.all().order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status', '')
    claim_type_filter = request.GET.get('claim_type', '')
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
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
    paginator = Paginator(claims, 20)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    # Status counts for summary
    status_counts = {
        'pending': RewardClaim.objects.filter(status='pending').count(),
        'processing': RewardClaim.objects.filter(status='processing').count(),
        'completed': RewardClaim.objects.filter(status='completed').count(),
        'cancelled': RewardClaim.objects.filter(status='cancelled').count(),
    }
    
    serializer = RewardClaimSerializer(page_obj, many=True)
    
    return Response({
        'success': True,
        'claims': serializer.data,
        'status_counts': status_counts,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })

@api_view(['POST'])
@token_required(['admin'])
def update_claim_status(request, claim_id):
    """API endpoint to update claim status"""
    try:
        claim = RewardClaim.objects.get(id=claim_id)
        new_status = request.data.get('status')
        
        if new_status not in ['processing', 'completed', 'cancelled']:
            return Response({
                'success': False,
                'error': 'Invalid status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate status transitions
        if new_status == 'completed' and claim.claim_amount < 500:
            return Response({
                'success': False,
                'error': 'Claims below 500 points cannot be completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_status == 'completed' and claim.status != 'processing':
            return Response({
                'success': False,
                'error': 'Only processing claims can be completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_status == 'completed' and claim.status == 'completed':
            return Response({
                'success': False,
                'error': 'Claim is already completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
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
        
        result_serializer = RewardClaimSerializer(claim)
        
        # Prepare success message
        if new_status == 'completed':
            message = f'Claim {claim.reference_id} completed successfully! {claim.claim_amount} points deducted from user.'
        else:
            message = f'Claim status updated to {new_status}'
        
        return Response({
            'success': True, 
            'message': message,
            'claim': result_serializer.data,
            'new_status': new_status
        })
        
    except RewardClaim.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Claim not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
