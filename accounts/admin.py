# from django.contrib import admin
# from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory
# from accounts.models import CustomUser, ActivityLog
# from dashboard.models import SystemSettings

# admin.site.register(CustomUser)
# admin.site.register(ActivityLog)
# admin.site.register(TrashSubmission)
# admin.site.register(CollectionRecord)
# admin.site.register(RewardPointHistory)
# admin.site.register(SystemSettings)



# # Register your models here.




from django.contrib import admin
from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory
from accounts.models import CustomUser, ActivityLog
from dashboard.models import SystemSettings


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'status', 'reward_points', 'created_at')
    list_filter = ('user_type', 'status', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'email', 'password', 'first_name', 'last_name', 'user_type', 'status')
        }),
        ('Contact Details', {
            'fields': ('phone', 'address', 'profile_image')
        }),
        ('Rewards', {
            'fields': ('reward_points',)
        }),
        ('Rider Information', {
            'fields': ('id_proof', 'vehicle_type', 'vehicle_model', 'license_plate', 'vehicle_color'),
            'classes': ('collapse',),
            'description': 'Rider-specific information'
        }),
        ('Important Dates', {
            'fields': ('created_at', 'updated_at', 'last_login', 'date_joined')
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('user', 'timestamp', 'action')
    search_fields = ('user__username', 'action', 'details')
    readonly_fields = ('user', 'action', 'timestamp', 'details')


@admin.register(TrashSubmission)
class TrashSubmissionAdmin(admin.ModelAdmin):
    list_display = ('track_id', 'user', 'trash_description', 'quantity_kg', 'location', 'status', 'created_at', 'rider')
    list_filter = ('status', 'created_at', 'rider')
    search_fields = ('track_id', 'user__username', 'trash_description', 'location', 'rider__username')
    readonly_fields = ('track_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Submission Information', {
            'fields': ('track_id', 'user', 'trash_description', 'quantity_kg', 'location', 'status')
        }),
        ('Rider Assignment', {
            'fields': ('rider', 'assigned_at')
        }),
        ('Progress Tracking', {
            'fields': ('pickup_time', 'completion_time', 'rider_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CollectionRecord)
class CollectionRecordAdmin(admin.ModelAdmin):
    list_display = ('submission', 'rider', 'trash_type', 'actual_quantity', 'points_awarded', 'collected_at', 'admin_verified')
    list_filter = ('admin_verified', 'collected_at', 'trash_type')
    search_fields = ('submission__track_id', 'rider__username', 'trash_type')
    readonly_fields = ('collected_at',)
    fieldsets = (
        ('Collection Details', {
            'fields': ('submission', 'rider', 'trash_type', 'actual_quantity', 'points_awarded')
        }),
        ('Verification', {
            'fields': ('admin_verified', 'verified_by', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('collected_at',)
        }),
    )


@admin.register(RewardPointHistory)
class RewardPointHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'reason', 'submission', 'awarded_by', 'created_at')
    list_filter = ('created_at', 'awarded_by')
    search_fields = ('user__username', 'reason', 'submission__track_id', 'awarded_by__username')
    readonly_fields = ('created_at',)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('maintenance_mode', 'debug_mode', 'log_level', 'updated_at')
    list_filter = ('maintenance_mode', 'debug_mode', 'log_level')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message', 'debug_mode', 'log_level')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent creating multiple settings instances
        return SystemSettings.objects.count() == 0
    
    actions = ['reset_to_defaults']
    
    @admin.action(description="Reset selected settings to defaults")
    def reset_to_defaults(self, request, queryset):
        for settings in queryset:
            SystemSettings.reset_to_defaults()
        self.message_user(request, "Settings have been reset to defaults")