from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import CustomUser

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.location = request.POST.get('location', '')
        
        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']
        
        # Rider-specific fields
        if user.user_type == 'rider':
            user.vehicle_type = request.POST.get('vehicle_type', '')
            user.vehicle_model = request.POST.get('vehicle_model', '')
            user.license_plate = request.POST.get('license_plate', '')
            user.vehicle_color = request.POST.get('vehicle_color', '')
            
            if request.FILES.get('id_proof'):
                user.id_proof = request.FILES['id_proof']
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/edit_profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})
