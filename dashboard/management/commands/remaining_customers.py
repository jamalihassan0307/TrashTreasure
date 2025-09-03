from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta, datetime
import random
import re
from decimal import Decimal
from difflib import SequenceMatcher
from accounts.models import CustomUser
from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory

class Command(BaseCommand):
    help = 'Create demo data for remaining customers with collection records'

    def handle(self, *args, **options):
        self.stdout.write('Creating remaining customers with collection data...')
        
        # Create users
        self.create_remaining_users()
        
        # Create submissions and collection records from actual data
        self.create_remaining_collections_from_data()
        
        # Also create some random submissions for users without collection data
        self.create_remaining_submissions()
        self.create_remaining_collections()
        
        self.stdout.write(self.style.SUCCESS('Remaining customers and collection data created successfully!'))

    def create_remaining_users(self):
        """Create remaining customers as users"""
        remaining_customers = [
            {"name": "M Imran", "address": "207 C block military account", "phone": "3334423760"},
            {"name": "Shoaib Sajid", "address": "259 B block punjab university housing scheme", "phone": "3116740433"},
            {"name": "Munawar Mahmood", "address": "33 C1 valancia", "phone": "3004207081"},
            {"name": "Husnain", "address": "44 A B1 Nishemen iqbal", "phone": "3350742632"},
            {"name": "Aysha Khurram", "address": "215 A Nisheman Iqbal", "phone": "3203182984"},
            {"name": "muhammad Ashraf", "address": "315 J block", "phone": "3004407027"},
            {"name": "Nouman", "address": "190 A Nishamen iqbal", "phone": "3212440554"},
            {"name": "Maqsood", "address": "195/A Nisheman iqbal", "phone": "3334327551"},
            {"name": "shaista", "address": "109 A nasheman iqbal", "phone": "3332377534"},
            {"name": "nadia", "address": "109/A nasheman iqbal", "phone": "3332377534"},
            {"name": "Muhammad Anees", "address": "112/A Nasheman iqbal", "phone": "3355500700"},
            {"name": "Abid niazi", "address": "113/A nasheman iqbal", "phone": "3344006478"},
            {"name": "Rana Shaheer", "address": "146 A nasheman iqbal", "phone": "3314483384"},
            {"name": "Syed uzair abbas", "address": "118 A nasheman iqbal", "phone": "3706800200"},
            {"name": "Mobashar Tahir", "address": "171/A nasheman iqbal", "phone": "3214075603"},
            {"name": "Ibrahim", "address": "249 A Nasheman iqbal", "phone": "3334538115"},
        ]
        
        for customer in remaining_customers:
            # Create username from name
            username = customer["name"].lower().replace(" ", "_").replace(".", "").replace("/", "_")
            email = f"{username}@example.com"
            
            # Split name into first and last name
            name_parts = customer["name"].split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            user, created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': make_password('recyclebin12'),
                    'user_type': 'customer',
                    'status': 'active',
                    'reward_points': 0,
                    'location': customer["address"],
                    'created_at': timezone.now() - timedelta(days=random.randint(30, 365))
                }
            )
            
            if created:
                self.stdout.write(f'Created user: {username}')

    def create_remaining_submissions(self):
        """Create trash submissions for remaining customers"""
        # Get all remaining users (military account, PUIHS, Valencia, Nishemen Iqbal)
        remaining_users = CustomUser.objects.filter(
            location__icontains='military account'
        ) | CustomUser.objects.filter(
            location__icontains='punjab university housing scheme'
        ) | CustomUser.objects.filter(
            location__icontains='valancia'
        ) | CustomUser.objects.filter(
            location__icontains='nishemen iqbal'
        ) | CustomUser.objects.filter(
            location__icontains='nasheman iqbal'
        ) | CustomUser.objects.filter(
            location__icontains='nishamen iqbal'
        )
        
        for user in remaining_users:
            # Create 1-3 submissions per user
            num_submissions = random.randint(1, 3)
            
            for i in range(num_submissions):
                submission = TrashSubmission.objects.create(
                    user=user,
                    quantity_kg=random.uniform(2.0, 8.0),
                    status='collected',
                    created_at=timezone.now() - timedelta(days=random.randint(1, 30))
                )
                self.stdout.write(f'Created submission for {user.username}: {submission.quantity_kg}kg')

    def create_remaining_collections(self):
        """Create collection records for remaining customers"""
        # Get all collected submissions
        submissions = TrashSubmission.objects.filter(status='collected').filter(
            user__location__icontains='military account'
        ) | TrashSubmission.objects.filter(status='collected').filter(
            user__location__icontains='punjab university housing scheme'
        ) | TrashSubmission.objects.filter(status='collected').filter(
            user__location__icontains='valancia'
        ) | TrashSubmission.objects.filter(status='collected').filter(
            user__location__icontains='nishemen iqbal'
        ) | TrashSubmission.objects.filter(status='collected').filter(
            user__location__icontains='nasheman iqbal'
        ) | TrashSubmission.objects.filter(status='collected').filter(
            user__location__icontains='nishamen iqbal'
        )
        
        for submission in submissions:
            # Check if collection record already exists
            if not hasattr(submission, 'collection_record'):
                # Create collection record
                collection = CollectionRecord.objects.create(
                    submission=submission,
                    rider=None,  # No rider assigned
                    trash_type='other',
                    actual_quantity=submission.quantity_kg + Decimal(str(random.uniform(-0.5, 0.5))),
                    points_awarded=int(submission.quantity_kg * 20),  # 20 points per kg
                    collected_at=submission.created_at + timedelta(hours=random.randint(1, 24)),
                    admin_verified=True
                )
                
                # Update user's reward points
                submission.user.reward_points += collection.points_awarded
                submission.user.save()
                
                self.stdout.write(f'Created collection record for {submission.user.username}: {collection.actual_quantity}kg, {collection.points_awarded} points')

    def similarity(self, a, b):
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def extract_house_number(self, address):
        """Extract house number from address"""
        match = re.match(r'^(\d+)', address.strip())
        if match:
            return match.group(1)
        return None

    def normalize_address(self, address):
        """Normalize address for better matching"""
        if not address:
            return ""
        normalized = re.sub(r'\s+', ' ', address.lower().strip())
        normalized = normalized.replace('street', 'st').replace('block', 'blk')
        return normalized

    def find_matching_collections(self, user_address, collection_data):
        """Find collection records that match the user's address"""
        matches = []
        user_house_num = self.extract_house_number(user_address)
        user_normalized = self.normalize_address(user_address)
        
        for collection in collection_data:
            collection_address = collection.get('address', '')
            collection_house_num = self.extract_house_number(collection_address)
            collection_normalized = self.normalize_address(collection_address)
            
            if user_house_num and collection_house_num and user_house_num == collection_house_num:
                # Check for military account, PUIHS, Valencia, or Nishemen Iqbal
                if any(keyword in user_normalized and keyword in collection_normalized 
                      for keyword in ['military account', 'puihs', 'valencia', 'nishemen iqbal', 'nasheman iqbal']):
                    matches.append(collection)
            elif self.similarity(user_normalized, collection_normalized) > 0.7:
                matches.append(collection)
        
        return matches

    def create_remaining_collections_from_data(self):
        """Create collection records from actual collection data"""
        # Collection data for remaining customers (military account, PUIHS, Valencia, Nishemen Iqbal)
        collection_data_2024 = [
            {"date": "12/04/2024", "address": "259 D PUIHS", "weight": "10", "points": "200"},
            {"date": "11/04/2024", "address": "257 C block millitary account", "weight": "2.4", "points": "48"},
            {"date": "11/28/2024", "address": "215 A Nishaman iqbal", "weight": "5.9", "points": "120"},
            {"date": "09/26/2024", "address": "259 D block PUEHS", "weight": "5.1", "points": "122"},
        ]
        
        collection_data_2025 = [
            {"date": "07.05.25", "address": "109 a nishemen iqbal", "weight": "2.4", "points": "48"},
            {"date": "07.05.25", "address": "146 a nishemen iqbal", "weight": "2.5", "points": "50"},
            {"date": "07.05.25", "address": "112 a nishemen iqbal", "weight": "2.6", "points": "52"},
            {"date": "15.04.25", "address": "118 a nishemen iqbal", "weight": "2.8", "points": "56"},
            {"date": "15.04.25", "address": "109a nishemen iqbal", "weight": "3.6", "points": "72"},
            {"date": "15.04.25", "address": "113a nishemen iqbal", "weight": "3.3", "points": "66"},
            {"date": "16.04.25", "address": "nishemen Iqbal 146 A", "weight": "4", "points": "80"},
            {"date": "16.04.25", "address": "171 a nishemen iqbal", "weight": "3.5", "points": "70"},
            {"date": "16.04.25", "address": "249 a nishemen iqbal", "weight": "3.6", "points": "72"},
            {"date": "24.04.25", "address": "197b nishemen iqbal", "weight": "2.2", "points": "44"},
            {"date": "24.04.25", "address": "171 b nishemen iqbal", "weight": "3", "points": "60"},
        ]
        
        all_collection_data = collection_data_2024 + collection_data_2025
        
        # Get all remaining users
        remaining_users = CustomUser.objects.filter(
            location__icontains='military account'
        ) | CustomUser.objects.filter(
            location__icontains='punjab university housing scheme'
        ) | CustomUser.objects.filter(
            location__icontains='valancia'
        ) | CustomUser.objects.filter(
            location__icontains='nishemen iqbal'
        ) | CustomUser.objects.filter(
            location__icontains='nasheman iqbal'
        ) | CustomUser.objects.filter(
            location__icontains='nishamen iqbal'
        )
        
        for user in remaining_users:
            # Find matching collections for this user
            matching_collections = self.find_matching_collections(user.location, all_collection_data)
            
            for collection in matching_collections:
                # Parse date
                try:
                    if '/' in collection['date']:
                        if len(collection['date'].split('/')) == 3:
                            if collection['date'].count('/') == 2:
                                date_parts = collection['date'].split('/')
                                if len(date_parts[2]) == 4:
                                    if int(date_parts[0]) > 12:
                                        collection_date = datetime.strptime(collection['date'], '%d/%m/%Y')
                                    else:
                                        collection_date = datetime.strptime(collection['date'], '%m/%d/%Y')
                                else:
                                    if int(date_parts[0]) > 12:
                                        collection_date = datetime.strptime(collection['date'], '%d/%m/%y')
                                    else:
                                        collection_date = datetime.strptime(collection['date'], '%m/%d/%y')
                            else:
                                collection_date = datetime.strptime(collection['date'], '%d/%m/%y')
                        else:
                            collection_date = datetime.strptime(collection['date'], '%d/%m/%y')
                    else:
                        collection_date = datetime.strptime(collection['date'], '%d.%m.%y')
                except:
                    collection_date = timezone.now() - timedelta(days=random.randint(1, 365))
                
                # Create submission
                try:
                    weight = float(collection.get('weight', 0)) if collection.get('weight') else random.uniform(2.0, 8.0)
                except (ValueError, TypeError):
                    weight = random.uniform(2.0, 8.0)
                submission = TrashSubmission.objects.create(
                    user=user,
                    quantity_kg=weight,
                    status='collected',
                    created_at=collection_date
                )
                
                # Create collection record
                try:
                    points = int(collection.get('points', 0)) if collection.get('points') else int(weight * 20)
                except (ValueError, TypeError):
                    points = int(weight * 20)
                collection_record = CollectionRecord.objects.create(
                    submission=submission,
                    rider=None,
                    trash_type='other',
                    actual_quantity=weight,
                    points_awarded=points,
                    collected_at=collection_date + timedelta(hours=random.randint(1, 24)),
                    admin_verified=True
                )
                
                # Update user's reward points
                user.reward_points += points
                user.save()
                
                self.stdout.write(f'Created collection from data for {user.username}: {weight}kg, {points} points on {collection_date.strftime("%Y-%m-%d")}')

# Collection data in JSON format
collection_data_json = {
    "collection_data_2024": [
        {"date": "12/04/2024", "address": "259 D PUIHS", "weight": "10", "points": "200"},
        {"date": "11/04/2024", "address": "257 C block millitary account", "weight": "2.4", "points": "48"},
        {"date": "11/28/2024", "address": "215 A Nishaman iqbal", "weight": "5.9", "points": "120"},
        {"date": "09/26/2024", "address": "259 D block PUEHS", "weight": "5.1", "points": "122"},
    ],
    "collection_data_2025": [
        {"date": "07.05.25", "address": "109 a nishemen iqbal", "weight": "2.4", "points": "48"},
        {"date": "07.05.25", "address": "146 a nishemen iqbal", "weight": "2.5", "points": "50"},
        {"date": "07.05.25", "address": "112 a nishemen iqbal", "weight": "2.6", "points": "52"},
        {"date": "15.04.25", "address": "118 a nishemen iqbal", "weight": "2.8", "points": "56"},
        {"date": "15.04.25", "address": "109a nishemen iqbal", "weight": "3.6", "points": "72"},
        {"date": "15.04.25", "address": "113a nishemen iqbal", "weight": "3.3", "points": "66"},
        {"date": "16.04.25", "address": "nishemen Iqbal 146 A", "weight": "4", "points": "80"},
        {"date": "16.04.25", "address": "171 a nishemen iqbal", "weight": "3.5", "points": "70"},
        {"date": "16.04.25", "address": "249 a nishemen iqbal", "weight": "3.6", "points": "72"},
        {"date": "24.04.25", "address": "197b nishemen iqbal", "weight": "2.2", "points": "44"},
        {"date": "24.04.25", "address": "171 b nishemen iqbal", "weight": "3", "points": "60"},
    ],
    "total_collections": 15,
    "generated_at": "2024-12-19T10:30:00.000Z"
}