from django.db import models
from django.utils.crypto import get_random_string
from accounts.models import CustomUser

# Create your models here.

class TrashSubmission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned to Rider'),
        ('on_the_way', 'Rider On The Way'),
        ('arrived', 'Rider Arrived at Location'),
        ('picked', 'Trash Picked Up'),
        ('collected', 'Collection Verified'),
        ('cancelled', 'Cancelled'),
    )
    
    track_id = models.CharField(max_length=15, unique=True, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submissions')
    quantity_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Estimated Weight (kg)")
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rider = models.ForeignKey(CustomUser, null=True, blank=True, 
                             on_delete=models.SET_NULL, 
                             related_name='assigned_collections',
                             limit_choices_to={'user_type': 'rider'})
    assigned_at = models.DateTimeField(null=True, blank=True)
    pickup_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    rider_notes = models.TextField(blank=True, null=True, verbose_name="Rider's Notes")
    
    def save(self, *args, **kwargs):
        if not self.track_id:
            self.track_id = self.generate_track_id()
        super().save(*args, **kwargs)
    
    def generate_track_id(self):
        return f"TR{get_random_string(8, allowed_chars='0123456789ABCDEF')}"
    
    def __str__(self):
        return f"#{self.track_id} - Submission by {self.user.username}"

class CollectionRecord(models.Model):
    submission = models.OneToOneField(TrashSubmission, on_delete=models.CASCADE, related_name='collection_record')
    rider = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.CASCADE, related_name='collections')
    trash_type = models.CharField(max_length=50, verbose_name="Actual Trash Type")
    actual_quantity = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Actual Weight (kg)")
    points_awarded = models.PositiveIntegerField(default=0, verbose_name="Reward Points")
    collected_at = models.DateTimeField(auto_now_add=True)
    admin_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(CustomUser, null=True, blank=True, 
                                  on_delete=models.SET_NULL,
                                  related_name='verified_collections',
                                  limit_choices_to={'user_type': 'admin'})
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Collection of #{self.submission.track_id}"

class RewardPointHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='point_history')
    points = models.IntegerField()
    reason = models.CharField(max_length=255)
    submission = models.ForeignKey(TrashSubmission, null=True, blank=True, on_delete=models.SET_NULL)
    awarded_by = models.ForeignKey(CustomUser, null=True, blank=True, 
                                  on_delete=models.SET_NULL,
                                  related_name='awarded_points',
                                  limit_choices_to={'user_type__in': ['rider', 'admin']})
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}: {self.points} points"
        
class RewardClaim(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'In Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    CLAIM_TYPE_CHOICES = (
        ('payment', 'Payment'),
        ('donation', 'Donation'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reward_claims')
    claim_amount = models.PositiveIntegerField(verbose_name="Points to Claim")
    monetary_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monetary Amount (Rs)", default=0)
    claim_type = models.CharField(max_length=10, choices=CLAIM_TYPE_CHOICES)
    donation_hospital = models.CharField(max_length=100, blank=True, null=True, verbose_name="Donation Hospital")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_by = models.ForeignKey(CustomUser, null=True, blank=True, 
                                    on_delete=models.SET_NULL,
                                    related_name='processed_claims',
                                    limit_choices_to={'user_type': 'admin'})
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    reference_id = models.CharField(max_length=20, blank=True, unique=True, editable=False)
    
    def save(self, *args, **kwargs):
        if not self.reference_id:
            self.reference_id = self.generate_reference_id()
        
        # Calculate monetary amount (10 Rs per point)
        self.monetary_amount = self.claim_amount * 10
        
        super().save(*args, **kwargs)
    
    def generate_reference_id(self):
        return f"CL{get_random_string(10, allowed_chars='0123456789ABCDEFGHJKLMNPQRSTUVWXYZ')}"
    
    def __str__(self):
        return f"{self.user.username}: {self.claim_amount} points - {self.get_status_display()}"
