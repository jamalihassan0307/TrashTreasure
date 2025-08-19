from django.contrib import admin
from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory
from accounts.models import CustomUser, ActivityLog
from dashboard.models import SystemSettings

admin.site.register(CustomUser)
admin.site.register(ActivityLog)
admin.site.register(TrashSubmission)
admin.site.register(CollectionRecord)
admin.site.register(RewardPointHistory)
admin.site.register(SystemSettings)



# Register your models here.
