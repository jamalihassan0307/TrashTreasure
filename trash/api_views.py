from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from .models import TrashSubmission, CollectionRecord, RewardPointHistory
from .serializers import (
    TrashSubmissionSerializer, 
    CollectionRecordSerializer,
    RewardPointHistorySerializer
)
from accounts.utils import token_required, get_user_id_by_token

@api_view(['POST'])
@token_required()
def submit_trash(request):
    """Submit new trash collection request"""
    serializer = TrashSubmissionSerializer(data=request.data)
    if serializer.is_valid():
        submission = serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@token_required()
def get_user_submissions(request):
    """Get all submissions for the current user"""
    # Apply filters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    
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
            Q(trash_description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    serializer = TrashSubmissionSerializer(submissions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def track_submission(request, track_id):
    """Track submission by track ID (public endpoint)"""
    try:
        submission = TrashSubmission.objects.get(track_id=track_id)
        serializer = TrashSubmissionSerializer(submission)
        return Response(serializer.data)
    except TrashSubmission.DoesNotExist:
        return Response({'error': 'Submission not found'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@token_required()
def submission_detail(request, submission_id):
    """Get detailed submission info"""
    submission = TrashSubmission.objects.filter(id=submission_id).first()
    
    if not submission:
        return Response({'error': 'Submission not found'}, 
                      status=status.HTTP_404_NOT_FOUND)
    
    # Check permission
    if not (request.user == submission.user or 
            request.user.user_type in ['rider', 'admin'] or
            (request.user.user_type == 'rider' and submission.rider == request.user)):
        return Response({'error': 'Permission denied'}, 
                      status=status.HTTP_403_FORBIDDEN)
    
    serializer = TrashSubmissionSerializer(submission)
    return Response(serializer.data)

@api_view(['POST'])
@token_required(['rider'])
def update_submission_status(request, submission_id):
    """Update submission status (rider only)"""
    try:
        submission = TrashSubmission.objects.get(id=submission_id, rider=request.user)
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not new_status:
            return Response({'error': 'Status is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if new_status not in ['on_the_way', 'arrived', 'picked']:
            return Response({'error': 'Invalid status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            submission.status = new_status
            if new_status == 'on_the_way':
                submission.assigned_at = timezone.now()
            elif new_status == 'picked':
                submission.pickup_time = timezone.now()
            
            if notes:
                submission.rider_notes = notes
            
            submission.save()
        
        serializer = TrashSubmissionSerializer(submission)
        return Response(serializer.data)
        
    except TrashSubmission.DoesNotExist:
        return Response({'error': 'Submission not found'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required(['rider'])
def complete_collection(request, submission_id):
    """Complete a trash collection (rider only)"""
    try:
        submission = TrashSubmission.objects.get(id=submission_id, rider=request.user)
        
        if submission.status != 'picked':
            return Response({'error': 'Submission must be in picked status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CollectionRecordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            collection = serializer.save(
                submission=submission,
                rider=request.user
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
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except TrashSubmission.DoesNotExist:
        return Response({'error': 'Submission not found'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required(['admin'])
def assign_rider(request, submission_id):
    """Assign rider to submission (admin only)"""
    try:
        submission = TrashSubmission.objects.get(id=submission_id)
        rider_id = request.data.get('rider')
        notes = request.data.get('notes', '')
        
        if not rider_id:
            return Response({'error': 'Rider ID is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if submission.status != 'pending':
            return Response({'error': 'Submission is not in pending status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        from accounts.models import CustomUser
        rider = CustomUser.objects.filter(id=rider_id, user_type='rider').first()
        if not rider:
            return Response({'error': 'Invalid rider'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        submission.rider = rider
        submission.status = 'assigned'
        submission.assigned_at = timezone.now()
        submission.rider_notes = notes
        submission.save()
        
        serializer = TrashSubmissionSerializer(submission)
        return Response(serializer.data)
        
    except TrashSubmission.DoesNotExist:
        return Response({'error': 'Submission not found'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@token_required(['admin'])
def verify_collection(request, submission_id):
    """Verify collection and award points (admin only)"""
    try:
        submission = TrashSubmission.objects.get(id=submission_id)
        points = request.data.get('points')
        notes = request.data.get('notes', '')
        
        if not points:
            return Response({'error': 'Points are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if submission.status != 'collected':
            return Response({'error': 'Submission is not in collected status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            points = int(points)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid points format'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Update collection record
            collection = CollectionRecord.objects.get(submission=submission)
            collection.points_awarded = points
            collection.admin_verified = True
            collection.verified_by = request.user
            collection.verified_at = timezone.now()
            collection.save()
            
            # Update user points
            submission.user.reward_points += points
            submission.user.save()
            
            # Create reward point history
            RewardPointHistory.objects.create(
                user=submission.user,
                points=points,
                reason=f'Collection verified by admin - {notes}' if notes else 'Collection verified by admin',
                submission=submission,
                awarded_by=request.user
            )
            
            # Update submission status
            submission.status = 'verified'
            submission.save()
        
        serializer = CollectionRecordSerializer(collection)
        return Response(serializer.data)
        
    except TrashSubmission.DoesNotExist:
        return Response({'error': 'Submission not found'}, 
                      status=status.HTTP_404_NOT_FOUND)
    except CollectionRecord.DoesNotExist:
        return Response({'error': 'Collection record not found'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@token_required(['rider'])
def rider_collections(request):
    """Get rider's collection history"""
    collections = CollectionRecord.objects.filter(rider=request.user).order_by('-collected_at')
    
    # Apply filters
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    
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
    
    serializer = CollectionRecordSerializer(collections, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@token_required()
def user_points_history(request):
    """Get user's point history"""
    history = RewardPointHistory.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    type_filter = request.GET.get('type', '')
    date_filter = request.GET.get('date', '')
    
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
    
    serializer = RewardPointHistorySerializer(history, many=True)
    return Response(serializer.data)
