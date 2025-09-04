from rest_framework import serializers
from .models import TrashSubmission, CollectionRecord, RewardPointHistory, RewardClaim
from accounts.serializers import UserSerializer

class TrashSubmissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    rider = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TrashSubmission
        fields = '__all__'
        read_only_fields = ('track_id', 'user', 'status', 'rider', 'assigned_at', 
                          'pickup_time', 'completion_time', 'created_at', 'updated_at')

class TrashSubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrashSubmission
        fields = ('quantity_kg', 'rider_notes')

class CollectionRecordSerializer(serializers.ModelSerializer):
    submission = TrashSubmissionSerializer(read_only=True)
    rider = UserSerializer(read_only=True)
    verified_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CollectionRecord
        fields = '__all__'
        read_only_fields = ('rider', 'admin_verified', 'verified_by', 'verified_at', 'collected_at')

class CollectionRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionRecord
        fields = ('trash_type', 'actual_quantity', 'points_awarded')

class RewardPointHistorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    awarded_by = UserSerializer(read_only=True)
    submission = TrashSubmissionSerializer(read_only=True)
    
    class Meta:
        model = RewardPointHistory
        fields = '__all__'
        read_only_fields = ('user', 'awarded_by', 'created_at')

class RewardClaimSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    processed_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    claim_type_display = serializers.CharField(source='get_claim_type_display', read_only=True)
    
    class Meta:
        model = RewardClaim
        fields = '__all__'
        read_only_fields = ('user', 'monetary_amount', 'status', 'created_at', 'updated_at', 
                          'processed_by', 'processed_at', 'reference_id')

class RewardClaimCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardClaim
        fields = ('claim_amount', 'claim_type', 'donation_hospital')

class RewardClaimUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardClaim
        fields = ('status', 'notes')

class TrashSubmissionStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=TrashSubmission.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)

class RiderAssignmentSerializer(serializers.Serializer):
    rider = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)

class CollectionVerificationSerializer(serializers.Serializer):
    points = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True)
