from rest_framework import serializers
from .models import TrashSubmission, CollectionRecord, RewardPointHistory

class TrashSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrashSubmission
        fields = '__all__'
        read_only_fields = ('track_id', 'user', 'status', 'rider', 'assigned_at', 
                          'pickup_time', 'completion_time')

class CollectionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionRecord
        fields = '__all__'
        read_only_fields = ('rider', 'admin_verified', 'verified_by', 'verified_at')

class RewardPointHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardPointHistory
        fields = '__all__'
        read_only_fields = ('user', 'awarded_by')
