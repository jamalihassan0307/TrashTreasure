from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from accounts.models import CustomUser
from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory
from django.db.models import Count, Q, Sum
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse

def is_rider(user):
    return user.is_authenticated and user.user_type == 'rider'

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

def home(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'user':
            return redirect('dashboard:user_dashboard')
        elif request.user.user_type == 'rider':
            return redirect('dashboard:rider_dashboard')
        elif request.user.user_type == 'admin':
            return redirect('dashboard:admin_dashboard')
    
    # Get statistics for non-authenticated users
    total_users = CustomUser.objects.filter(user_type='user', status='active').count()
    total_submissions = TrashSubmission.objects.count()
    active_riders = CustomUser.objects.filter(user_type='rider', status='active').count()
    total_points = sum([user.reward_points for user in CustomUser.objects.all()])
    
    # Get environmental impact data from system settings
    from .models import SystemSettings
    try:
        environmental_data = SystemSettings.get_settings()
    except:
        environmental_data = None
    
    context = {
        'total_users': total_users,
        'total_submissions': total_submissions,
        'active_riders': active_riders,
        'total_points': total_points,
        'environmental_data': environmental_data,
    }
    return render(request, 'dashboard/home.html', context)

def about(request):
    # Get statistics for the about page
    total_users = CustomUser.objects.filter(user_type='user', status='active').count()
    total_submissions = TrashSubmission.objects.count()
    active_riders = CustomUser.objects.filter(user_type='rider', status='active').count()
    total_points = sum([user.reward_points for user in CustomUser.objects.all()])
    
    context = {
        'total_users': total_users,
        'total_submissions': total_submissions,
        'active_riders': active_riders,
        'total_points': total_points,
    }
    return render(request, 'dashboard/about.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.status == 'suspended':
                messages.error(request, 'Your account has been suspended. Please contact support.')
                return redirect('dashboard:login')
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            if user.user_type == 'user':
                return redirect('dashboard:user_dashboard')
            elif user.user_type == 'rider':
                return redirect('dashboard:rider_dashboard')
            elif user.user_type == 'admin':
                return redirect('dashboard:admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'dashboard/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('dashboard:home')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        location = request.POST.get('location')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'dashboard/register.html')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'dashboard/register.html')
        
        if not location or location.strip() == '':
            messages.error(request, 'Location is required.')
            return render(request, 'dashboard/register.html')
        
        # Only allow regular users to register
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password1,
            user_type='user',  # Force user type to 'user'
            location=location.strip()
        )
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('dashboard:login')
    
    return render(request, 'dashboard/register.html')

@login_required
@user_passes_test(lambda u: u.user_type == 'user')
def user_dashboard(request):
    user_submissions = TrashSubmission.objects.filter(user=request.user).order_by('-created_at')
    total_points = request.user.reward_points
    pending_submissions = user_submissions.filter(status='pending').count()
    completed_submissions = user_submissions.filter(status='collected').count()
    
    context = {
        'user_submissions': user_submissions,
        'total_points': total_points,
        'pending_submissions': pending_submissions,
        'completed_submissions': completed_submissions,
    }
    return render(request, 'dashboard/user_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'user')
def user_submissions(request):
    user_submissions = TrashSubmission.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    per_page = int(request.GET.get('per_page', 10))
    
    if status_filter:
        user_submissions = user_submissions.filter(status=status_filter)
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            user_submissions = user_submissions.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            user_submissions = user_submissions.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            user_submissions = user_submissions.filter(created_at__date__gte=month_ago)
    
    if search_query:
        user_submissions = user_submissions.filter(
            Q(trash_description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(user_submissions, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_submissions = user_submissions.count()
    pending_submissions = user_submissions.filter(status='pending').count()
    completed_submissions = user_submissions.filter(status='collected').count()
    total_points = request.user.reward_points
    
    context = {
        'user_submissions': page_obj,
        'total_submissions': total_submissions,
        'pending_submissions': pending_submissions,
        'completed_submissions': completed_submissions,
        'total_points': total_points,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
        'per_page': per_page,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    return render(request, 'dashboard/user_submissions.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'user')
def user_points(request):
    # Get user's point history
    point_history = RewardPointHistory.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    type_filter = request.GET.get('type', '')
    date_filter = request.GET.get('date', '')
    per_page = int(request.GET.get('per_page', 10))
    
    if type_filter:
        if type_filter == 'earned':
            point_history = point_history.filter(points__gt=0)
        elif type_filter == 'spent':
            point_history = point_history.filter(points__lt=0)
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            point_history = point_history.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            point_history = point_history.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            point_history = point_history.filter(created_at__date__gte=month_ago)
    
    # Pagination
    paginator = Paginator(point_history, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_points = request.user.reward_points
    total_earned = point_history.filter(points__gt=0).aggregate(Sum('points'))['points__sum'] or 0
    total_spent = abs(point_history.filter(points__lt=0).aggregate(Sum('points'))['points__sum'] or 0)
    submissions_count = TrashSubmission.objects.filter(user=request.user).count()
    completed_count = TrashSubmission.objects.filter(user=request.user, status='collected').count()
    
    context = {
        'point_history': page_obj,
        'total_points': total_points,
        'total_earned': total_earned,
        'total_spent': total_spent,
        'submissions_count': submissions_count,
        'completed_count': completed_count,
        'type_filter': type_filter,
        'date_filter': date_filter,
        'per_page': per_page,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    return render(request, 'dashboard/user_points.html', context)

@login_required
@user_passes_test(is_rider)
def rider_dashboard(request):
    assigned_submissions = TrashSubmission.objects.filter(
        rider=request.user,
        status__in=['assigned', 'on_the_way', 'arrived', 'picked']
    ).order_by('-assigned_at')
    
    # Counts for dashboard stats
    total_assignments = TrashSubmission.objects.filter(
        rider=request.user
    ).count()
    
    pending_collections = assigned_submissions.count()
    
   
    
    total_completed = TrashSubmission.objects.filter(
        rider=request.user,
        status__in=['collected']
    ).count()
    
    context = {
        'assigned_submissions': assigned_submissions,
        'total_assignments': total_assignments,
        'pending_collections': pending_collections,
        'total_completed': total_completed,
    }
    return render(request, 'dashboard/rider_dashboard.html', context)

@login_required
@user_passes_test(is_rider)
def rider_earnings(request):
    # Get rider's collection history
    collection_history = CollectionRecord.objects.filter(rider=request.user).order_by('-collected_at')
    
    # Apply filters
    date_filter = request.GET.get('date', '')
    search_query = request.GET.get('search', '')
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            collection_history = collection_history.filter(collected_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            collection_history = collection_history.filter(collected_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            collection_history = collection_history.filter(collected_at__date__gte=month_ago)
    
    if search_query:
        collection_history = collection_history.filter(
            Q(submission__location__icontains=search_query) |
            Q(trash_type__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(collection_history, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    collections_this_month = collection_history.filter(
        collected_at__month=timezone.now().month
    ).count()
    collections_today = collection_history.filter(
        collected_at__date=timezone.now().date()
    ).count()
    
    
    # Calculate performance metrics
    total_weight = collection_history.aggregate(Sum('actual_quantity'))['actual_quantity__sum'] or 0
    total_points_awarded = collection_history.aggregate(Sum('points_awarded'))['points_awarded__sum'] or 0
    
    # Mock data for demo
    avg_completion_time = 2.5  # hours
    avg_rating = 4.8
    
    context = {
        'collection_history': page_obj,
        'collections_this_month': collections_this_month,
        'collections_today': collections_today,
        'avg_rating': avg_rating,
        'avg_completion_time': avg_completion_time,
        'total_weight': total_weight,
        'total_points_awarded': total_points_awarded,
        'date_filter': date_filter,
        'search_query': search_query,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    return render(request, 'dashboard/rider_earnings.html', context)

@login_required
@user_passes_test(is_rider)
def rider_assigned_collections(request):
    """View for riders to see their assigned collections with filtering and sorting"""
    
    # Get all collections assigned to the current rider
    assigned_submissions = TrashSubmission.objects.filter(
        rider=request.user
    ).select_related('user').order_by('-updated_at')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        assigned_submissions = assigned_submissions.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Apply status filter if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        assigned_submissions = assigned_submissions.filter(status=status_filter)
    
    # Apply sorting
    sort_order = request.GET.get('sort', 'updated_at')
    if sort_order == 'created_at':
        assigned_submissions = assigned_submissions.order_by('-created_at')
    elif sort_order == 'priority':
        # Note: Priority field doesn't exist in current model, but keeping for future use
        assigned_submissions = assigned_submissions.order_by('-updated_at')
    elif sort_order == 'location':
        assigned_submissions = assigned_submissions.order_by('location')
    else:  # Default: updated_at
        assigned_submissions = assigned_submissions.order_by('-updated_at')
    
    # Pagination
    per_page = int(request.GET.get('per_page', 10))
    paginator = Paginator(assigned_submissions, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'assigned_submissions': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_order': sort_order,
        'per_page': per_page,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    
    return render(request, 'dashboard/rider_assigned_collections_rider.html', context)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    total_submissions = TrashSubmission.objects.count()
    pending_submissions = TrashSubmission.objects.filter(status='pending').count()
    active_riders = CustomUser.objects.filter(user_type='rider', status='active').count()
    active_riders_list = CustomUser.objects.filter(user_type='rider', status='active')
    total_points = sum([user.reward_points for user in CustomUser.objects.all()])
    
    # Recent submissions with pagination
    recent_submissions_query = TrashSubmission.objects.all().order_by('-created_at')
    recent_per_page = int(request.GET.get('per_page', 10))
    recent_paginator = Paginator(recent_submissions_query, recent_per_page)
    recent_page_number = request.GET.get('page', 1)
    recent_submissions = recent_paginator.get_page(recent_page_number)
    
    # Weekly collections data with proper date calculations
    now = timezone.now()
    
    # Get start of current week (Monday)
    days_since_monday = now.weekday()
    start_of_week = now - timedelta(days=days_since_monday)
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get start of previous week
    start_of_prev_week = start_of_week - timedelta(days=7)
    end_of_prev_week = start_of_week - timedelta(seconds=1)
    
    # Count collections for current and previous week
    this_week_collections = CollectionRecord.objects.filter(
        collected_at__gte=start_of_week
    ).count()
    
    last_week_collections = CollectionRecord.objects.filter(
        collected_at__gte=start_of_prev_week,
        collected_at__lte=end_of_prev_week
    ).count()
    
    # Calculate weekly growth
    weekly_growth = 0
    if last_week_collections > 0:
        weekly_growth = round(((this_week_collections - last_week_collections) / last_week_collections) * 100)
    elif this_week_collections > 0:
        weekly_growth = 100  # If last week was 0 but this week has collections
    
    # Monthly progress with dynamic goal based on total submissions
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_collections = CollectionRecord.objects.filter(collected_at__gte=month_start).count()
    
    # Set monthly goal based on total submissions (more realistic goal)
    monthly_goal = max(10, total_submissions // 12)  # At least 10, or 1/12th of total submissions
    monthly_progress = min(round((monthly_collections / monthly_goal) * 100), 100) if monthly_goal > 0 else 0
    
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
    
    # Additional metrics for enhanced dashboard
    # Calculate system health metrics
    total_collections = CollectionRecord.objects.count()
    completion_rate = round((total_collections / total_submissions * 100), 1) if total_submissions > 0 else 0
    
    # Get recent activity (last 24 hours)
    yesterday = now - timedelta(days=1)
    new_submissions_24h = TrashSubmission.objects.filter(created_at__gte=yesterday).count()
    new_collections_24h = CollectionRecord.objects.filter(collected_at__gte=yesterday).count()
    new_users_24h = CustomUser.objects.filter(created_at__gte=yesterday).count()
    
    # Calculate average response time (time from submission to assignment)
    response_times = []
    submissions_with_riders = TrashSubmission.objects.filter(
        rider__isnull=False,
        assigned_at__isnull=False
    )
    
    for submission in submissions_with_riders:
        if submission.assigned_at and submission.created_at:
            time_diff = submission.assigned_at - submission.created_at
            response_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
    
    avg_response_time = round(sum(response_times) / len(response_times), 1) if response_times else 0
    
    # Get top performing riders
    top_riders = CustomUser.objects.filter(user_type='rider').annotate(
        collection_count=Count('collections')
    ).order_by('-collection_count')[:5]
    
    user_submissions = TrashSubmission.objects.all().order_by('-created_at')
    completed_submissions_weight = user_submissions.filter(status='collected').aggregate(Sum('quantity_kg'))['quantity_kg__sum'] or 0
    # Calculate efficiency metrics
    total_weight_collected = CollectionRecord.objects.aggregate(Sum('actual_quantity'))['actual_quantity__sum'] or 0
    avg_collections_per_day = round(total_collections / 30, 1) if total_collections > 0 else 0
    
    # Get system status indicators
    system_status = 'Operational'
    if pending_submissions > total_submissions * 0.3:  # If more than 30% are pending
        system_status = 'High Load'
    elif avg_response_time > 24:  # If average response time > 24 hours
        system_status = 'Slow Response'
    
    context = {
        'total_users': total_users,
        'total_submissions': total_submissions,
        'pending_submissions': pending_submissions,
        'active_riders': active_riders,
        'active_riders_list': active_riders_list,
        'total_points': total_points,
        'recent_submissions': recent_submissions,
        'this_week_collections': this_week_collections,
        'last_week_collections': last_week_collections,
        'weekly_growth': weekly_growth,
        'monthly_progress': monthly_progress,
        'monthly_goal': monthly_goal,
        'monthly_collections': monthly_collections,
        'daily_collections': daily_collections,
        'daily_labels': daily_labels,
        'completion_rate': completion_rate,
        'new_submissions_24h': new_submissions_24h,
        'new_collections_24h': new_collections_24h,
        'new_users_24h': new_users_24h,
        'avg_response_time': avg_response_time,
        'top_riders': top_riders,
        'completed_submissions_weight': completed_submissions_weight,
        'total_weight_collected': total_weight_collected,
        'avg_collections_per_day': avg_collections_per_day,
        'system_status': system_status,
        'recent_per_page': recent_per_page,
        'recent_paginator': recent_paginator,
        'recent_page_obj': recent_submissions,
        'recent_is_paginated': recent_paginator.num_pages > 1,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_analytics(request):
    # Get filter type and parameters
    filter_type = request.GET.get('filter_type', 'period')
    period = int(request.GET.get('period', 30))
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Calculate date range based on filter type
    if filter_type == 'date' and start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        # Add time to end date to include the entire day
        end = end.replace(hour=23, minute=59, second=59)
        is_custom_date_range = True
    else:
        end = timezone.now()
        start = end - timedelta(days=period)
        is_custom_date_range = False
    
    # Get current period data
    current_users = CustomUser.objects.filter(created_at__gte=start).count()
    current_submissions = TrashSubmission.objects.filter(created_at__gte=start).count()
    current_riders = CustomUser.objects.filter(user_type='rider', created_at__gte=start).count()
    current_points = sum([user.reward_points for user in CustomUser.objects.filter(created_at__gte=start)])
    
    # Get previous period data for comparison
    prev_start = start - timedelta(days=period)
    prev_users = CustomUser.objects.filter(created_at__gte=prev_start, created_at__lt=start).count()
    prev_submissions = TrashSubmission.objects.filter(created_at__gte=prev_start, created_at__lt=start).count()
    prev_riders = CustomUser.objects.filter(user_type='rider', created_at__gte=prev_start, created_at__lt=start).count()
    prev_points = sum([user.reward_points for user in CustomUser.objects.filter(created_at__gte=prev_start, created_at__lt=start)])
    
    # Calculate growth percentages
    user_growth = ((current_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
    submission_growth = ((current_submissions - prev_submissions) / prev_submissions * 100) if prev_submissions > 0 else 0
    rider_growth = ((current_riders - prev_riders) / prev_riders * 100) if prev_riders > 0 else 0
    points_growth = ((current_points - prev_points) / prev_points * 100) if prev_points > 0 else 0
    
    # Get real data for insights
    avg_daily_registrations = current_users / period if period > 0 else 0
    
    # Calculate average response time (time from submission to assignment)
    response_times = []
    submissions_with_riders = TrashSubmission.objects.filter(
        rider__isnull=False,
        assigned_at__isnull=False,
        created_at__gte=start
    )
    
    for submission in submissions_with_riders:
        if submission.assigned_at and submission.created_at:
            time_diff = submission.assigned_at - submission.created_at
            response_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
    
    avg_response_time = round(sum(response_times) / len(response_times), 1) if response_times else 0
    
    # Get total weight collected in period
    total_weight = CollectionRecord.objects.filter(
        collected_at__gte=start
    ).aggregate(Sum('actual_quantity'))['actual_quantity__sum'] or 0
    
    # Get total collections in period
    total_collections = CollectionRecord.objects.filter(
        collected_at__gte=start
    ).count()
    
    # Calculate completion ratio
    total_submissions_in_period = TrashSubmission.objects.filter(created_at__gte=start).count()
    completed_submissions_in_period = TrashSubmission.objects.filter(
        created_at__gte=start,
        status='collected'
    ).count()
    
    completion_ratio = round((completed_submissions_in_period / total_submissions_in_period) * 100, 1) if total_submissions_in_period > 0 else 0
    
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
    
    # Additional performance metrics
    # Calculate average collection time (time from assignment to collection)
    collection_times = []
    completed_collections = CollectionRecord.objects.filter(
        collected_at__gte=start,
        submission__assigned_at__isnull=False
    )
    
    for collection in completed_collections:
        if collection.submission.assigned_at and collection.collected_at:
            time_diff = collection.collected_at - collection.submission.assigned_at
            collection_times.append(time_diff.total_seconds() / 3600)  # Convert to hours
    
    avg_collection_time = round(sum(collection_times) / len(collection_times), 1) if collection_times else 0
    
    # Calculate efficiency metrics
    total_distance_covered = total_collections * 5.2  # Mock data - in real app, calculate actual distance
    avg_collections_per_day = round(total_collections / period, 1) if period > 0 else 0
    
    # Get top performing locations
    top_locations = TrashSubmission.objects.filter(
        created_at__gte=start
    ).values('location').annotate(
        submission_count=Count('id')
    ).order_by('-submission_count')[:5]
    
    location_labels = []
    location_counts = []
    
    for location in top_locations:
        location_labels.append(location['location'][:20] + '...' if len(location['location']) > 20 else location['location'])
        location_counts.append(location['submission_count'])
    
    # Calculate system health metrics
    total_submissions_all = TrashSubmission.objects.count()  # Total submissions across all time
    pending_ratio = round((TrashSubmission.objects.filter(status='pending').count() / total_submissions_all * 100), 1) if total_submissions_all > 0 else 0
    active_user_ratio = round((CustomUser.objects.filter(status='active').count() / CustomUser.objects.count() * 100), 1) if CustomUser.objects.count() > 0 else 0
    
    # Get daily activity for the last 30 days
    daily_activity = []
    daily_activity_labels = []
    
    for i in range(30):
        date = end - timedelta(days=i)
        submissions_count = TrashSubmission.objects.filter(created_at__date=date.date()).count()
        collections_count = CollectionRecord.objects.filter(collected_at__date=date.date()).count()
        daily_activity.append({
            'submissions': submissions_count,
            'collections': collections_count
        })
        daily_activity_labels.insert(0, date.strftime('%b %d'))
    
    # Calculate trend indicators
    recent_submissions = daily_activity[-7:]  # Last 7 days
    previous_submissions = daily_activity[-14:-7]  # 7 days before that
    
    recent_avg = sum(day['submissions'] for day in recent_submissions) / 7 if recent_submissions else 0
    previous_avg = sum(day['submissions'] for day in previous_submissions) / 7 if previous_submissions else 0
    
    submission_trend = round(((recent_avg - previous_avg) / previous_avg * 100), 1) if previous_avg > 0 else 0
    
    # Generate custom date range data if using date filter
    custom_date_labels = []
    custom_submission_data = []
    custom_user_type_labels = []
    custom_user_type_counts = []
    custom_daily_labels = []
    custom_daily_activity = []
    
    if is_custom_date_range:
        # Generate daily data for custom date range
        current_date = start.date()
        end_date_obj = end.date()
        
        while current_date <= end_date_obj:
            submissions_count = TrashSubmission.objects.filter(created_at__date=current_date).count()
            collections_count = CollectionRecord.objects.filter(collected_at__date=current_date).count()
            
            custom_daily_activity.append({
                'submissions': submissions_count,
                'collections': collections_count
            })
            custom_daily_labels.append(current_date.strftime('%b %d'))
            
            current_date += timedelta(days=1)
        
        # Generate submission data for custom range (daily breakdown)
        custom_submission_data = [day['submissions'] for day in custom_daily_activity]
        custom_date_labels = custom_daily_labels
        
        # Get user type distribution for custom date range
        custom_user_types = CustomUser.objects.filter(created_at__gte=start, created_at__lte=end).values('user_type').annotate(count=Count('user_type'))
        for user_type in custom_user_types:
            custom_user_type_labels.append(user_type['user_type'].title())
            custom_user_type_counts.append(user_type['count'])
    else:
        # Use default data for period filter
        custom_date_labels = daily_activity_labels
        custom_submission_data = [day['submissions'] for day in daily_activity]
        custom_user_type_labels = user_type_labels
        custom_user_type_counts = user_type_counts
        custom_daily_labels = daily_activity_labels
        custom_daily_activity = daily_activity
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'filter_type': filter_type,
        'is_custom_date_range': is_custom_date_range,
        'total_users': current_users,
        'total_submissions': current_submissions,
        'active_riders': current_riders,
        'total_points': current_points,
        'user_growth': user_growth,
        'submission_growth': submission_growth,
        'rider_growth': rider_growth,
        'points_growth': points_growth,
        'avg_daily_registrations': avg_daily_registrations,
        'avg_response_time': avg_response_time,
        'total_weight': total_weight,
        'completion_ratio': completion_ratio,
        'monthly_submissions': monthly_submissions,
        'monthly_labels': monthly_labels,
        'user_type_labels': user_type_labels,
        'user_type_counts': user_type_counts,
        'rider_names': rider_names,
        'rider_performance': rider_performance,
        'avg_collection_time': avg_collection_time,
        'total_distance_covered': total_distance_covered,
        'avg_collections_per_day': avg_collections_per_day,
        'location_labels': location_labels,
        'location_counts': location_counts,
        'pending_ratio': pending_ratio,
        'active_user_ratio': active_user_ratio,
        'daily_activity': daily_activity,
        'daily_activity_labels': daily_activity_labels,
        'submission_trend': submission_trend,
        # Custom date range data
        'custom_date_labels': custom_date_labels,
        'custom_submission_data': custom_submission_data,
        'custom_user_type_labels': custom_user_type_labels,
        'custom_user_type_counts': custom_user_type_counts,
        'custom_daily_labels': custom_daily_labels,
        'custom_daily_activity': custom_daily_activity,
    }
    return render(request, 'dashboard/admin_analytics.html', context)

@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    from .models import SystemSettings
    from accounts.models import CustomUser
    from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory
    from django.db import connection
    
    if request.method == 'POST':
        section = request.POST.get('section')
        action = request.POST.get('action')
        
        if action == 'clear_data':
            try:
                # Clear all data from all tables
                RewardPointHistory.objects.all().delete()
                CollectionRecord.objects.all().delete()
                TrashSubmission.objects.all().delete()
                
                # Clear all non-admin users
                CustomUser.objects.exclude(user_type='admin').delete()
                
                # Reset admin reward points
                admin_users = CustomUser.objects.filter(user_type='admin')
                for admin in admin_users:
                    admin.reward_points = 0
                    admin.save()
                
                messages.success(request, 'All data has been cleared successfully!')
            except Exception as e:
                messages.error(request, f'Error clearing data: {str(e)}')
            return redirect('dashboard:admin_settings')
        
        elif action == 'reset_system':
            try:
                # Reset system settings to defaults
                SystemSettings.reset_to_defaults()
                messages.success(request, 'System has been reset to default settings!')
            except Exception as e:
                messages.error(request, f'Error resetting system: {str(e)}')
            return redirect('dashboard:admin_settings')
        
        elif section == 'general':
            try:
                settings = SystemSettings.get_settings()
                settings.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
                settings.maintenance_message = request.POST.get('maintenance_message')
                settings.debug_mode = request.POST.get('debug_mode') == 'on'
                settings.log_level = request.POST.get('log_level')
                settings.save()
                messages.success(request, 'General settings updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating general settings: {str(e)}')
            return redirect('dashboard:admin_settings')
        
        elif section == 'environmental':
            try:
                settings = SystemSettings.get_settings()
                settings.co2_reduction_tons = int(request.POST.get('co2_reduction_tons', 15))
                settings.water_saved_gallons = int(request.POST.get('water_saved_gallons', 1000))
                settings.landfill_space_acres = int(request.POST.get('landfill_space_acres', 10))
                settings.trees_saved_count = int(request.POST.get('trees_saved_count', 500))
                settings.save()
                messages.success(request, 'Environmental impact data updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating environmental data: {str(e)}')
            return redirect('dashboard:admin_settings')
        
        else:
            messages.success(request, f'{section.title()} settings updated successfully!')
            return redirect('dashboard:admin_settings')
    
    # Get settings from database
    try:
        settings = SystemSettings.get_settings()
    except:
        # Fallback to defaults if database error
        settings = {
            'site_name': 'Recycle Bin',
            'site_description': 'Transform waste into rewards with our eco-friendly recycling platform',
            'contact_email': 'admin@trashtotreasure.com',
            'default_timezone': 'UTC',
            'maintenance_mode': False,
            'maintenance_message': 'System is currently under maintenance. Please check back later.',
            'debug_mode': False,
            'log_level': 'INFO',
        }
    
    context = {
        'settings': settings,
    }
    return render(request, 'dashboard/admin_settings.html', context)

def maintenance_page(request):
    """Maintenance page for users when system is in maintenance mode"""
    from .models import SystemSettings
    
    try:
        settings = SystemSettings.get_settings()
    except:
        settings = {
            'maintenance_message': 'System is currently under maintenance. Please check back later.'
        }
    
    context = {
        'settings': settings,
    }
    return render(request, 'dashboard/maintenance.html', context)

def under_construction_page(request):
    """Under construction page for users when system is in debug mode"""
    from .models import SystemSettings
    
    try:
        settings = SystemSettings.get_settings()
    except:
        settings = {
            'maintenance_message': 'Website is under construction. Please check back later.'
        }
    
    context = {
        'settings': settings,
    }
    return render(request, 'dashboard/under_construction.html', context)

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    user_type_filter = request.GET.get('user_type', '')
    status_filter = request.GET.get('status', '')
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
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'status_filter': status_filter,
        'per_page': per_page,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    return render(request, 'dashboard/manage_users.html', context)

@login_required
@user_passes_test(is_admin)
def create_rider(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'dashboard/create_rider.html')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'dashboard/create_rider.html')
        
        # Create rider account
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            location=address,
            user_type='rider'
        )
        messages.success(request, f'Rider account created successfully for {username}!')
        return redirect('dashboard:manage_users')
    
    return render(request, 'dashboard/create_rider.html')

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def toggle_user_status(request, user_id):
    """Toggle user status between active and suspended"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        
        if user.user_type == 'admin':
            messages.error(request, 'Cannot modify admin user status.')
            return redirect('dashboard:manage_users')
        
        # Toggle status
        if user.status == 'active':
            user.status = 'suspended'
            action = 'suspended'
        else:
            user.status = 'active'
            action = 'activated'
        
        user.save()
        
        # Log the action
        # ActivityLog.objects.create(
        #     user=request.user,
        #     action='toggled_user_status',
        #     details={
        #         'target_user_id': user.id,
        #         'target_username': user.username,
        #         'old_status': 'suspended' if action == 'activated' else 'active',
        #         'new_status': action,
        #         'admin_user': request.user.username
        #     }
        # )
        
        messages.success(request, f'User {user.username} has been {action}.')
        
    except Exception as e:
        messages.error(request, f'Error updating user status: {str(e)}')
    
    return redirect('dashboard:manage_users')

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def clear_user_points(request, user_id):
    """Clear all reward points for a specific user"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            
            if user.user_type == 'admin':
                return JsonResponse({'success': False, 'error': 'Cannot modify admin user points.'})
            
            # Store the old points value for logging
            old_points = user.reward_points
            
            # Clear the points
            user.reward_points = 0
            user.save()
            
            # Log the action
            # ActivityLog.objects.create(
            #     user=request.user,
            #     action='cleared_user_points',
            #     details={
            #         'target_user_id': user.id,
            #         'target_username': user.username,
            #         'old_points': old_points,
            #         'new_points': 0,
            #         'admin_user': request.user.username
            #     }
            # )
            
            return JsonResponse({
                'success': True,
                'message': f'Points cleared successfully for {user.username}'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def award_bonus_points(request):
    """Award bonus points to a user with reason"""
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            points = int(request.POST.get('points', 0))
            reason = request.POST.get('reason', '').strip()
            
            if not user_id or not points or not reason:
                return JsonResponse({'success': False, 'error': 'All fields are required.'})
            
            if points < 1 or points > 10000:
                return JsonResponse({'success': False, 'error': 'Points must be between 1 and 10,000.'})
            
            user = get_object_or_404(CustomUser, id=user_id)
            
            if user.user_type == 'admin':
                return JsonResponse({'success': False, 'error': 'Cannot modify admin user points.'})
            
            # Store the old points value
            old_points = user.reward_points
            
            # Add bonus points
            user.reward_points += points
            user.save()
            
            # Create reward point history entry
            RewardPointHistory.objects.create(
                user=user,
                points=points,
                reason=f"Bonus: {reason}",
                awarded_by=request.user
            )
            
            # Log the action
            # ActivityLog.objects.create(
            #     user=request.user,
            #     action='awarded_bonus_points',
            #     details={
            #         'target_user_id': user.id,
            #         'target_username': user.username,
            #         'points_awarded': points,
            #         'old_points': old_points,
            #         'new_points': user.reward_points,
            #         'reason': reason,
            #         'admin_user': request.user.username
            #     }
            # )
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully awarded {points} bonus points to {user.username}',
                'username': user.username,
                'points_awarded': points,
                'new_total': user.reward_points
            })
            
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid points value.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def contact(request):
    return render(request, 'dashboard/contact.html')
