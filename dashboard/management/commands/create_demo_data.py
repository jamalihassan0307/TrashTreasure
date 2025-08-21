from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
import random
from accounts.models import CustomUser
from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory

class Command(BaseCommand):
    help = 'Create demo data for testing Trash to Treasure application'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')
        
        # Create demo users
        self.create_demo_users()
        
        # Create demo trash submissions
        self.create_demo_submissions()
        
        # Create demo collection records
        self.create_demo_collections()
        
        # Create demo reward point history
        self.create_demo_reward_history()
        
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))

    def create_demo_users(self):
        """Create demo users with different roles"""
        
        # Create regular users
        users_data = [
            {'username': 'user2', 'email': 'user2@demo.com', 'user_type': 'user'},
            {'username': 'user3', 'email': 'user3@demo.com', 'user_type': 'user'},
            {'username': 'user4', 'email': 'user4@demo.com', 'user_type': 'user'},
        ]
        
        for user_data in users_data:
            user, created = CustomUser.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'password': make_password('user12345'),
                    'user_type': user_data['user_type'],
                    'status': 'active',
                    'first_name': f"User{user_data['username'][-1]}",
                    'last_name': 'Demo',
                    'phone': f'+92 300 12345{user_data["username"][-1]}',
                    'address': f'Demo Address {user_data["username"][-1]}, Lahore, Pakistan',
                    'reward_points': random.randint(50, 500)
                }
            )
            if created:
                self.stdout.write(f'Created user: {user.username}')
        
        # Create admin users
        admins_data = [
            {'username': 'admin1', 'email': 'admin1@demo.com'},
            {'username': 'admin2', 'email': 'admin2@demo.com'},
            {'username': 'admin3', 'email': 'admin3@demo.com'},
        ]
        
        for admin_data in admins_data:
            admin, created = CustomUser.objects.get_or_create(
                username=admin_data['username'],
                defaults={
                    'email': admin_data['email'],
                    'password': make_password('user12345'),
                    'user_type': 'admin',
                    'status': 'active',
                    'first_name': f"Admin{admin_data['username'][-1]}",
                    'last_name': 'Demo',
                    'phone': f'+92 300 12345{admin_data["username"][-1]}',
                    'address': f'Demo Admin Address {admin_data["username"][-1]}, Lahore, Pakistan',
                    'reward_points': 0
                }
            )
            if created:
                self.stdout.write(f'Created admin: {admin.username}')
        
        # Create rider users
        riders_data = [
            {'username': 'rider2', 'email': 'rider2@demo.com'},
            {'username': 'rider3', 'email': 'rider3@demo.com'},
            {'username': 'rider4', 'email': 'rider4@demo.com'},
        ]
        
        for rider_data in riders_data:
            rider, created = CustomUser.objects.get_or_create(
                username=rider_data['username'],
                defaults={
                    'email': rider_data['email'],
                    'password': make_password('user12345'),
                    'user_type': 'rider',
                    'status': 'active',
                    'first_name': f"Rider{rider_data['username'][-1]}",
                    'last_name': 'Demo',
                    'phone': f'+92 300 12345{rider_data["username"][-1]}',
                    'address': f'Demo Rider Address {rider_data["username"][-1]}, Lahore, Pakistan',
                    'vehicle_type': random.choice(['Motorcycle', 'Car', 'Van']),
                    'vehicle_model': random.choice(['Honda Activa', 'Suzuki Swift', 'Toyota Hiace']),
                    'license_plate': f'LHR-{random.randint(1000, 9999)}',
                    'vehicle_color': random.choice(['Red', 'Blue', 'White', 'Black']),
                    'reward_points': random.randint(100, 1000)
                }
            )
            if created:
                self.stdout.write(f'Created rider: {rider.username}')

    def create_demo_submissions(self):
        """Create demo trash submissions with different statuses"""
        
        users = CustomUser.objects.filter(user_type='user')
        riders = CustomUser.objects.filter(user_type='rider')
        
        if not users.exists() or not riders.exists():
            self.stdout.write('No users or riders found. Please create users first.')
            return
        
        trash_types = [
            'Plastic bottles and containers',
            'Paper and cardboard waste',
            'Electronic waste (old phones, laptops)',
            'Glass bottles and jars',
            'Metal cans and scrap',
            'Organic waste and food scraps',
            'Textile waste (old clothes)',
            'Mixed household waste',
            'Construction debris',
            'Garden waste and leaves'
        ]
        
        locations = [
            'Gulberg III, Lahore',
            'DHA Phase 6, Lahore',
            'Model Town, Lahore',
            'Johar Town, Lahore',
            'Cantt Area, Lahore',
            'Allama Iqbal Town, Lahore',
            'Wapda Town, Lahore',
            'Garden Town, Lahore',
            'Faisal Town, Lahore',
            'Shadman, Lahore'
        ]
        
        statuses = ['pending', 'assigned', 'on_the_way', 'arrived', 'picked', 'collected', 'cancelled']
        
        # Create submissions over the last 30 days
        for i in range(20):
            user = random.choice(users)
            status = random.choice(statuses)
            created_at = timezone.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            
            submission = TrashSubmission.objects.create(
                user=user,
                trash_description=random.choice(trash_types),
                quantity_kg=round(random.uniform(0.5, 15.0), 2),
                location=random.choice(locations),
                status=status,
                created_at=created_at,
                updated_at=created_at
            )
            
            # Assign rider for non-pending submissions
            if status != 'pending':
                rider = random.choice(riders)
                submission.rider = rider
                submission.assigned_at = created_at + timedelta(hours=random.randint(1, 6))
                
                if status in ['on_the_way', 'arrived', 'picked', 'collected']:
                    submission.pickup_time = submission.assigned_at + timedelta(hours=random.randint(1, 3))
                
                if status == 'collected':
                    submission.completion_time = submission.pickup_time + timedelta(hours=random.randint(1, 2))
                
                submission.save()
            
            self.stdout.write(f'Created submission: {submission.track_id} - {submission.status}')

    def create_demo_collections(self):
        """Create demo collection records for completed submissions"""
        
        completed_submissions = TrashSubmission.objects.filter(status='collected')
        
        for submission in completed_submissions:
            # Check if collection record already exists
            if hasattr(submission, 'collection_record'):
                continue
                
            collection = CollectionRecord.objects.create(
                submission=submission,
                rider=submission.rider,
                trash_type=submission.trash_description,
                actual_quantity=round(random.uniform(0.5, 20.0), 2),
                points_awarded=random.randint(10, 100),
                collected_at=submission.completion_time or submission.updated_at,
                admin_verified=random.choice([True, False])
            )
            
            if collection.admin_verified:
                collection.verified_by = CustomUser.objects.filter(user_type='admin').first()
                collection.verified_at = collection.collected_at + timedelta(hours=random.randint(1, 24))
                collection.save()
            
            self.stdout.write(f'Created collection record for: {submission.track_id}')

    def create_demo_reward_history(self):
        """Create demo reward point history"""
        
        users = CustomUser.objects.filter(user_type='user')
        riders = CustomUser.objects.filter(user_type='rider')
        admins = CustomUser.objects.filter(user_type='admin')
        
        reasons = [
            'Trash collection completed',
            'Bonus for large quantity',
            'Special recycling bonus',
            'Referral bonus',
            'Monthly activity bonus',
            'Holiday special bonus',
            'Quality bonus',
            'Speed bonus',
            'Regular user bonus',
            'Environmental impact bonus'
        ]
        
        # Create reward history for users
        for user in users:
            # Create 3-8 reward history entries per user
            for i in range(random.randint(3, 8)):
                points = random.randint(5, 50)
                reason = random.choice(reasons)
                
                # Get a random submission for this user
                submission = user.submissions.first()
                
                # Randomly assign points by admin or rider
                awarded_by = random.choice(list(riders) + list(admins)) if riders.exists() or admins.exists() else None
                
                RewardPointHistory.objects.create(
                    user=user,
                    points=points,
                    reason=reason,
                    submission=submission,
                    awarded_by=awarded_by,
                    created_at=timezone.now() - timedelta(days=random.randint(0, 30))
                )
            
            self.stdout.write(f'Created reward history for user: {user.username}')
        
        # Create reward history for riders
        for rider in riders:
            # Create 2-5 reward history entries per rider
            for i in range(random.randint(2, 5)):
                points = random.randint(10, 100)
                reason = random.choice([
                    'Collection completed',
                    'Bonus for quick service',
                    'Customer satisfaction bonus',
                    'Weekly performance bonus',
                    'Special assignment bonus'
                ])
                
                # Get a random collection for this rider
                collection = CollectionRecord.objects.filter(rider=rider).first()
                
                awarded_by = random.choice(list(admins)) if admins.exists() else None
                
                RewardPointHistory.objects.create(
                    user=rider,
                    points=points,
                    reason=reason,
                    submission=collection.submission if collection else None,
                    awarded_by=awarded_by,
                    created_at=timezone.now() - timedelta(days=random.randint(0, 30))
                )
            
            self.stdout.write(f'Created reward history for rider: {rider.username}')
