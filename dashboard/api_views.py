from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Sum
from datetime import timedelta
from django.db import transaction

from .models import SystemSettings
from .serializers import SystemSettingsSerializer
from accounts.models import CustomUser
from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory
from accounts.utils import token_required

@api_view(['GET'])
def get_public_stats(request):
    """Get public statistics for non-authenticated users"""
    total_users = CustomUser.objects.filter(user_type='user', status='active').count()
    total_submissions = TrashSubmission.objects.count()
    active_riders = CustomUser.objects.filter(user_type='rider', status='active').count()
    total_points = sum([user.reward_points for user in CustomUser.objects.all()])
    
    return Response({
        'total_users': total_users,
        'total_submissions': total_submissions,
        'active_riders': active_riders,
        'total_points': total_points,
    })

@api_view(['GET'])
@token_required()
def get_user_dashboard_stats(request):
    """Get dashboard statistics for regular users"""
    user_submissions = TrashSubmission.objects.filter(user=request.user)
    total_points = request.user.reward_points
    pending_submissions = user_submissions.filter(status='pending').count()
    completed_submissions = user_submissions.filter(status='collected').count()
    
    return Response({
        'total_points': total_points,
        'pending_submissions': pending_submissions,
        'completed_submissions': completed_submissions,
        'total_submissions': user_submissions.count()
    })

@api_view(['GET'])
@token_required(['rider'])
def get_rider_dashboard_stats(request):
    """Get dashboard statistics for riders"""
    assigned_submissions = TrashSubmission.objects.filter(
        rider=request.user,
        status__in=['assigned', 'on_the_way', 'arrived', 'picked']
    ).order_by('-assigned_at')
    
    completed_today = CollectionRecord.objects.filter(
        rider=request.user,
        collected_at__date=timezone.now().date()
    ).count()
    
    total_completed = CollectionRecord.objects.filter(rider=request.user).count()
    
    serializer = TrashSubmissionSerializer(assigned_submissions, many=True)
    
    return Response({
        'assigned_submissions': serializer.data,
        'completed_today': completed_today,
        'total_completed': total_completed
    })

@api_view(['GET'])
@token_required(['admin'])
def get_admin_dashboard_stats(request):
    """Get comprehensive dashboard statistics for admins"""
    now = timezone.now()
    
    # Basic stats
    total_users = CustomUser.objects.count()
    total_submissions = TrashSubmission.objects.count()
    pending_submissions = TrashSubmission.objects.filter(status='pending').count()
    active_riders = CustomUser.objects.filter(user_type='rider', status='active').count()
    total_points = sum([user.reward_points for user in CustomUser.objects.all()])
    
    # Recent submissions
    recent_submissions = TrashSubmissionSerializer(
        TrashSubmission.objects.all().order_by('-created_at')[:10],
        many=True
    ).data
    
    # Weekly stats
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_prev_week = start_of_week - timedelta(days=7)
    
    this_week_collections = CollectionRecord.objects.filter(
        collected_at__gte=start_of_week
    ).count()
    
    last_week_collections = CollectionRecord.objects.filter(
        collected_at__gte=start_of_prev_week,
        collected_at__lt=start_of_week
    ).count()
    
    # Calculate weekly growth
    weekly_growth = 0
    if last_week_collections > 0:
        weekly_growth = round(((this_week_collections - last_week_collections) / last_week_collections) * 100)
    elif this_week_collections > 0:
        weekly_growth = 100
    
    # System health metrics
    total_collections = CollectionRecord.objects.count()
    completion_rate = round((total_collections / total_submissions * 100), 1) if total_submissions > 0 else 0
    
    # Recent activity
    yesterday = now - timedelta(days=1)
    new_submissions_24h = TrashSubmission.objects.filter(created_at__gte=yesterday).count()
    new_collections_24h = CollectionRecord.objects.filter(collected_at__gte=yesterday).count()
    new_users_24h = CustomUser.objects.filter(created_at__gte=yesterday).count()
    
    # Top performing riders
    top_riders = CustomUser.objects.filter(user_type='rider').annotate(
        collection_count=Count('collections')
    ).order_by('-collection_count')[:5]
    
    return Response({
        'basic_stats': {
            'total_users': total_users,
            'total_submissions': total_submissions,
            'pending_submissions': pending_submissions,
            'active_riders': active_riders,
            'total_points': total_points,
        },
        'recent_submissions': recent_submissions,
        'weekly_stats': {
            'this_week_collections': this_week_collections,
            'last_week_collections': last_week_collections,
            'weekly_growth': weekly_growth,
        },
        'system_health': {
            'completion_rate': completion_rate,
            'new_submissions_24h': new_submissions_24h,
            'new_collections_24h': new_collections_24h,
            'new_users_24h': new_users_24h,
        },
        'top_riders': [{
            'id': rider.id,
            'username': rider.username,
            'collection_count': rider.collection_count
        } for rider in top_riders]
    })

@api_view(['GET'])
@token_required(['admin'])
def get_admin_analytics(request):
    """Get detailed analytics data for admins"""
    # Get period filter
    period = int(request.GET.get('period', 30))
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Calculate date range
    if start_date and end_date:
        start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
        end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end = timezone.now()
        start = end - timedelta(days=period)
    
    # Current period data
    current_users = CustomUser.objects.filter(created_at__gte=start).count()
    current_submissions = TrashSubmission.objects.filter(created_at__gte=start).count()
    current_riders = CustomUser.objects.filter(user_type='rider', created_at__gte=start).count()
    current_points = sum([user.reward_points for user in CustomUser.objects.filter(created_at__gte=start)])
    
    # Previous period data
    prev_start = start - timedelta(days=period)
    prev_users = CustomUser.objects.filter(created_at__gte=prev_start, created_at__lt=start).count()
    prev_submissions = TrashSubmission.objects.filter(created_at__gte=prev_start, created_at__lt=start).count()
    
    # Growth calculations
    user_growth = ((current_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
    submission_growth = ((current_submissions - prev_submissions) / prev_submissions * 100) if prev_submissions > 0 else 0
    
    return Response({
        'period_stats': {
            'current_users': current_users,
            'current_submissions': current_submissions,
            'current_riders': current_riders,
            'current_points': current_points,
        },
        'growth_stats': {
            'user_growth': user_growth,
            'submission_growth': submission_growth,
        },
        'date_range': {
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'period': period,
        }
    })

@api_view(['GET', 'PUT'])
@token_required(['admin'])
def manage_system_settings(request):
    """Get or update system settings"""
    settings = SystemSettings.get_settings()
    
    if request.method == 'GET':
        serializer = SystemSettingsSerializer(settings)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@token_required(['admin'])
def reset_system_settings(request):
    """Reset system settings to defaults"""
    try:
        settings = SystemSettings.reset_to_defaults()
        serializer = SystemSettingsSerializer(settings)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@token_required(['admin'])
def clear_system_data(request):
    """Clear all system data (admin only)"""
    try:
        with transaction.atomic():
            # Clear all data from all tables
            RewardPointHistory.objects.all().delete()
            CollectionRecord.objects.all().delete()
            TrashSubmission.objects.all().delete()
            
            # Clear all non-admin users
            CustomUser.objects.exclude(user_type='admin').delete()
            
            # Reset admin reward points
            CustomUser.objects.filter(user_type='admin').update(reward_points=0)
        
        return Response({'message': 'All system data cleared successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
