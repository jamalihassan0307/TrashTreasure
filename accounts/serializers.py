from rest_framework import serializers
from .models import CustomUser, ActivityLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 
                 'reward_points', 'profile_image', 'location', 'status', 'user_type')
        read_only_fields = ('reward_points', 'user_type', 'status')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class RiderSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('id_proof', 'vehicle_type', 
                'vehicle_model', 'license_plate', 'vehicle_color')

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'
