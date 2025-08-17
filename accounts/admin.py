from django.contrib import admin
from accounts.models import CustomUser, ActivityLog
from dashboard.models import SystemSettings

admin.site.register(CustomUser)
admin.site.register(ActivityLog)
admin.site.register(SystemSettings)



# Register your models here.
