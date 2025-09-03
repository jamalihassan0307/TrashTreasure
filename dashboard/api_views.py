from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Sum
from datetime import timedelta
from django.db import transaction
from django.core.paginator import Paginator

from .models import SystemSettings
from .serializers import SystemSettingsSerializer
from accounts.models import CustomUser
from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory, RewardClaim
from accounts.utils import token_required

@api_view(['GET'])
def get_public_stats(request):
    """Get public statistics for non-authenticated users"""
    try:
        total_users = CustomUser.objects.filter(user_type='user', status='active').count()
        total_submissions = TrashSubmission.objects.count()
        active_riders = CustomUser.objects.filter(user_type='rider', status='active').count()
        total_points = sum([user.reward_points for user in CustomUser.objects.all()])
        
        return Response({
            'success': True,
            'total_users': total_users,
            'total_submissions': total_submissions,
            'active_riders': active_riders,
            'total_points': total_points,
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@token_required()
def get_user_dashboard_stats(request):
    """Get dashboard statistics for regular users"""
    try:
        user_submissions = TrashSubmission.objects.filter(user=request.user)
        total_points = request.user.reward_points
        pending_submissions = user_submissions.filter(status='pending').count()
        completed_submissions = user_submissions.filter(status='collected').count()
        total_submissions = user_submissions.count()
        
        # Get recent submissions
        recent_submissions = user_submissions.order_by('-created_at')[:5]
        from trash.serializers import TrashSubmissionSerializer
        recent_serializer = TrashSubmissionSerializer(recent_submissions, many=True)
        
        return Response({
            'success': True,
            'total_points': total_points,
            'pending_submissions': pending_submissions,
            'completed_submissions': completed_submissions,
            'total_submissions': total_submissions,
            'recent_submissions': recent_serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@token_required(['rider'])
def get_rider_dashboard_stats(request):
    """Get dashboard statistics for riders"""
    try:
        assigned_submissions = TrashSubmission.objects.filter(
            rider=request.user,
            status__in=['assigned', 'on_the_way', 'arrived', 'picked']
        ).order_by('-assigned_at')
        
        completed_today = CollectionRecord.objects.filter(
            rider=request.user,
            collected_at__date=timezone.now().date()
        ).count()
        
        total_completed = CollectionRecord.objects.filter(rider=request.user).count()
        
        # Get recent collections
        recent_collections = CollectionRecord.objects.filter(
            rider=request.user
        ).order_by('-collected_at')[:5]
        
        from trash.serializers import TrashSubmissionSerializer, CollectionRecordSerializer
        submissions_serializer = TrashSubmissionSerializer(assigned_submissions, many=True)
        collections_serializer = CollectionRecordSerializer(recent_collections, many=True)
        
        return Response({
            'success': True,
            'assigned_submissions': submissions_serializer.data,
            'completed_today': completed_today,
            'total_completed': total_completed,
            'recent_collections': collections_serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@token_required(['admin'])
def get_admin_dashboard_stats(request):
    """Get comprehensive dashboard statistics for admins"""
    try:
        now = timezone.now()
        
        # Basic stats
        total_users = CustomUser.objects.count()
        total_submissions = TrashSubmission.objects.count()
        pending_submissions = TrashSubmission.objects.filter(status='pending').count()
        active_riders = CustomUser.objects.filter(user_type='rider', status='active').count()
        total_points = sum([user.reward_points for user in CustomUser.objects.all()])
        
        # Recent submissions
        recent_submissions = TrashSubmission.objects.all().order_by('-created_at')[:10]
        from trash.serializers import TrashSubmissionSerializer
        recent_serializer = TrashSubmissionSerializer(recent_submissions, many=True)
    
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
        
            # Get daily collection data for the chart
        daily_collections = []
        daily_labels = []
            
        for i in range(7):
            date = start_of_week + timedelta(days=i)
            count = CollectionRecord.objects.filter(
                collected_at__date=date.date()
            ).count()
            daily_collections.append(count)
            daily_labels.append(date.strftime('%a'))
            
        return Response({
                'success': True,
            'basic_stats': {
                'total_users': total_users,
                'total_submissions': total_submissions,
                'pending_submissions': pending_submissions,
                'active_riders': active_riders,
                'total_points': total_points,
            },
                'recent_submissions': recent_serializer.data,
            'weekly_stats': {
                'this_week_collections': this_week_collections,
                'last_week_collections': last_week_collections,
                'weekly_growth': weekly_growth,
                    'daily_collections': daily_collections,
                    'daily_labels': daily_labels,
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
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@token_required(['admin'])
def get_admin_analytics(request):
    """Get detailed analytics data for admins"""
    try:
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
        
            # Get monthly submission trends for the last 6 months
        monthly_submissions = []
        monthly_labels = []
            
        for i in range(6):
            month_start = end.replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(seconds=1)
            
            count = TrashSubmission.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            monthly_submissions.insert(0, count)
            monthly_labels.insert(0, month_start.strftime('%b %Y'))
            
            # Get user type distribution
            user_types = CustomUser.objects.values('user_type').annotate(count=Count('user_type'))
            user_type_labels = []
            user_type_counts = []
            
            for user_type in user_types:
                user_type_labels.append(user_type['user_type'].title())
                user_type_counts.append(user_type['count'])
            
            # Get rider performance data
            rider_performance = []
            rider_names = []
            
            top_riders = CustomUser.objects.filter(user_type='rider').annotate(
                collection_count=Count('collections')
            ).order_by('-collection_count')[:10]
            
            for rider in top_riders:
                rider_names.append(rider.username)
                rider_performance.append(rider.collection_count)
        
        return Response({
                'success': True,
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
                'trends': {
                    'monthly_submissions': monthly_submissions,
                    'monthly_labels': monthly_labels,
                    'user_type_labels': user_type_labels,
                    'user_type_counts': user_type_counts,
                    'rider_names': rider_names,
                    'rider_performance': rider_performance,
                },
            'date_range': {
                'start_date': start.strftime('%Y-%m-%d'),
                'end_date': end.strftime('%Y-%m-%d'),
                'period': period,
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT'])
@token_required(['admin'])
def manage_system_settings(request):
    """Get or update system settings"""
    try:
        settings = SystemSettings.get_settings()
        
        if request.method == 'GET':
            serializer = SystemSettingsSerializer(settings)
            return Response({
                    'success': True,
                    'settings': serializer.data
                })
        
        elif request.method == 'PUT':
            serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                        'success': True,
                        'message': 'System settings updated successfully',
                        'settings': serializer.data
                    })
                return Response({
                    'success': False,
                    'error': 'Invalid data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@token_required(['admin'])
def reset_system_settings(request):
    """Reset system settings to defaults"""
    try:
        settings = SystemSettings.reset_to_defaults()
        serializer = SystemSettingsSerializer(settings)
        return Response({
            'success': True,
            'message': 'System settings reset to defaults successfully',
            'settings': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        
        return Response({
            'success': True,
            'message': 'All system data cleared successfully'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@token_required(['admin'])
def get_user_management_data(request):
    """Get user management data for admins"""
    try:
        # Get search and filter parameters
        search_query = request.GET.get('search', '')
        user_type_filter = request.GET.get('user_type', '')
        status_filter = request.GET.get('status', '')
        page = request.GET.get('page', 1)
        per_page = int(request.GET.get('per_page', 10))
        
        # Start with all users except admins
        users = CustomUser.objects.exclude(user_type='admin')
        
        # Apply filters
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        if user_type_filter:
            users = users.filter(user_type=user_type_filter)
        
        if status_filter:
            users = users.filter(status=status_filter)
        
        # Order by creation date
        users = users.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(users, per_page)
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        from accounts.serializers import UserSerializer
        serializer = UserSerializer(page_obj, many=True)
        
        # Get counts for summary
        total_users = users.count()
        active_users = users.filter(status='active').count()
        suspended_users = users.filter(status='suspended').count()
        riders_count = users.filter(user_type='rider').count()
        regular_users_count = users.filter(user_type='user').count()
        
        return Response({
            'success': True,
            'users': serializer.data,
            'summary': {
                'total_users': total_users,
                'active_users': active_users,
                'suspended_users': suspended_users,
                'riders_count': riders_count,
                'regular_users_count': regular_users_count,
            },
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'per_page': per_page,
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@token_required(['admin'])
def toggle_user_status(request, user_id):
    """Toggle user status between active and suspended"""
    try:
        user = CustomUser.objects.get(id=user_id)
        
        if user.user_type == 'admin':
            return Response({
                'success': False,
                'error': 'Cannot modify admin user status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Toggle status
        if user.status == 'active':
            user.status = 'suspended'
            action = 'suspended'
        else:
            user.status = 'active'
            action = 'activated'
        
        user.save()
        
        from accounts.serializers import UserSerializer
        serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'message': f'User {user.username} has been {action}',
            'user': serializer.data
        })
        
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@token_required(['admin'])
def clear_user_points(request, user_id):
    """Clear all reward points for a specific user"""
    try:
        user = CustomUser.objects.get(id=user_id)
        
        if user.user_type == 'admin':
            return Response({
                'success': False,
                'error': 'Cannot modify admin user points'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store the old points value for logging
        old_points = user.reward_points
        
        # Clear the points
        user.reward_points = 0
        user.save()
        
        from accounts.serializers import UserSerializer
        serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'message': f'Points cleared successfully for {user.username}',
            'user': serializer.data,
            'old_points': old_points,
            'new_points': 0
        })
        
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@token_required(['admin'])
def get_pending_submissions(request):
    """Get all pending submissions for admin management"""
    try:
        submissions = TrashSubmission.objects.filter(status='pending').order_by('-created_at')
        
        # Apply filters
        search_query = request.GET.get('search', '')
        date_filter = request.GET.get('date', '')
        page = request.GET.get('page', 1)
        per_page = int(request.GET.get('per_page', 10))
        
        if search_query:
            submissions = submissions.filter(
                Q(user__username__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        if date_filter:
            today = timezone.now().date()
            if date_filter == 'today':
                submissions = submissions.filter(created_at__date=today)
            elif date_filter == 'week':
                week_ago = today - timedelta(days=7)
                submissions = submissions.filter(created_at__date__gte=week_ago)
            elif date_filter == 'month':
                month_ago = today - timedelta(days=30)
                submissions = submissions.filter(created_at__date__gte=month_ago)
        
        # Pagination
        paginator = Paginator(submissions, per_page)
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        from trash.serializers import TrashSubmissionSerializer
        serializer = TrashSubmissionSerializer(page_obj, many=True)
        
        return Response({
            'success': True,
            'submissions': serializer.data,
            'total_pending': submissions.count(),
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'per_page': per_page,
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
