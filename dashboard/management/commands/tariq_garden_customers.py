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
    help = 'Create demo data for Tariq Garden customers with collection records'

    def handle(self, *args, **options):
        self.stdout.write('Creating Tariq Garden customers with collection data...')
        
        # Create users
        self.create_tariq_garden_users()
        
        # Create submissions and collection records from actual data
        self.create_tariq_garden_collections_from_data()
        
        # Also create some random submissions for users without collection data
        self.create_tariq_garden_submissions()
        self.create_tariq_garden_collections()
        
        self.stdout.write(self.style.SUCCESS('Tariq Garden customers and collection data created successfully!'))

    def create_tariq_garden_users(self):
        """Create Tariq Garden customers as users"""
        tariq_garden_customers = [
            {"name": "Faizan Ahmed", "address": "80 Street 3 B block tariq garden", "phone": "3060602393"},
            {"name": "M Tahir", "address": "107 C 2 block tariq garden", "phone": "3007746154"},
            {"name": "Arshad Baighum", "address": "46 H block tariq garden", "phone": "3114186858"},
            {"name": "Adeel Shaikh", "address": "44 F block 1st floor Tariq garden", "phone": "3214117084"},
            {"name": "Wasid Saleem", "address": "18 H block Tariq garden", "phone": "3009413404"},
            {"name": "Qaisar Pervaiz", "address": "54 H Tariq garden", "phone": "3224548196"},
            {"name": "Muzamil", "address": "51 H tariq garden", "phone": "3324267090"},
        ]
        
        for customer in tariq_garden_customers:
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

    def create_tariq_garden_submissions(self):
        """Create trash submissions for Tariq Garden customers"""
        # Get all Tariq Garden users
        tariq_garden_users = CustomUser.objects.filter(location__icontains='tariq garden')
        
        for user in tariq_garden_users:
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

    def create_tariq_garden_collections(self):
        """Create collection records for Tariq Garden customers"""
        # Get all collected submissions
        submissions = TrashSubmission.objects.filter(status='collected', user__location__icontains='tariq garden')
        
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
                if 'tariq garden' in user_normalized and 'tariq garden' in collection_normalized:
                    matches.append(collection)
            elif self.similarity(user_normalized, collection_normalized) > 0.7:
                matches.append(collection)
        
        return matches

    def create_tariq_garden_collections_from_data(self):
        """Create collection records from actual collection data"""
        # Tariq Garden collection data from 2024 and 2025
        collection_data_2024 = [
            {"date": "12/02/2024", "address": "37 H tariq garden", "weight": "3.9", "points": "80"},
            {"date": "12/04/2024", "address": "54 H tariq garden", "weight": "3.5", "points": "62"},
            {"date": "11/13/2024", "address": "80 B tariq garden", "weight": "5.1", "points": "102"},
            {"date": "11/18/2024", "address": "377 H block tariq garden", "weight": "2.6", "points": "52"},
            {"date": "11/18/2024", "address": "54 H tariq garden", "weight": "3.5", "points": "62"},
            {"date": "10/07/2024", "address": "80 B block Tariq Garden", "weight": "4.9", "points": "100"},
            {"date": "10/07/2024", "address": "54 H tariq garden", "weight": "3.6", "points": "72"},
            {"date": "10/19/2024", "address": "54 A block Tariq garden", "weight": "3.7", "points": "74"},
            {"date": "10/28/2024", "address": "80 B block Tariq Garden", "weight": "8.5", "points": "172"},
            {"date": "10/31/2024", "address": "54 H tariq garden", "weight": "2.3", "points": "46"},
            {"date": "09/04/2024", "address": "Qaisar 54 H Tariq Garden", "weight": "2.3", "points": "46"},
            {"date": "09/05/2024", "address": "46 H block tariq garden", "weight": "2.6", "points": "52"},
            {"date": "09/06/2024", "address": "109 H tariq garden", "weight": "4.2", "points": "84"},
            {"date": "09/13/2024", "address": "80 B block tariq garden", "weight": "4.5", "points": "90"},
            {"date": "09/18/2024", "address": "45 F block tariq garden", "weight": "10", "points": "200"},
            {"date": "09/24/2024", "address": "qaisar 54 H block tariq garden", "weight": "1.8", "points": "20"},
            {"date": "08/15/2024", "address": "45 F block tariq garden", "weight": "10", "points": "200"},
            {"date": "08/24/2024", "address": "qaisar 54 H block tariq garden", "weight": "1.8", "points": "20"},
        ]
        
        collection_data_2025 = [
            {"date": "05.05.25", "address": "37 h tarik garden", "weight": "2", "points": "40"},
            {"date": "05.05.25", "address": "54 h tarik garden", "weight": "4.5", "points": "90"},
            {"date": "09.04.25", "address": "37 h tarik garden", "weight": "2", "points": "40"},
            {"date": "09.04.25", "address": "54 h tarik garden", "weight": "3.5", "points": "70"},
            {"date": "15.04.25", "address": "54h tarik garden", "weight": "2", "points": "40"},
            {"date": "15.04.25", "address": "37 h tarik garden", "weight": "3", "points": "60"},
            {"date": "15.04.25", "address": "46 h tarik garden", "weight": "3.2", "points": "64"},
            {"date": "05.02.25", "address": "54 h tarik garden", "weight": "4.2", "points": "84"},
            {"date": "05.02.25", "address": "46 h tarik garden", "weight": "2.2", "points": "44"},
            {"date": "05.02.25", "address": "80 b tarik garden", "weight": "7", "points": "140"},
            {"date": "10.02.25", "address": "37 h tarik garden", "weight": "3.5", "points": "70"},
            {"date": "17.02.25", "address": "54 h tarik garden", "weight": "3.2", "points": "64"},
            {"date": "17.02.25", "address": "80 b tarik garden", "weight": "4.5", "points": "90"},
            {"date": "21.04.25", "address": "80 b tarik garden", "weight": "4.5", "points": "90"},
        ]
        
        all_collection_data = collection_data_2024 + collection_data_2025
        
        # Get all Tariq Garden users
        tariq_garden_users = CustomUser.objects.filter(location__icontains='tariq garden')
        
        for user in tariq_garden_users:
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
        {"date": "12/02/2024", "address": "37 H tariq garden", "weight": "3.9", "points": "80"},
        {"date": "12/04/2024", "address": "54 H tariq garden", "weight": "3.5", "points": "62"},
        {"date": "11/13/2024", "address": "80 B tariq garden", "weight": "5.1", "points": "102"},
        {"date": "11/18/2024", "address": "377 H block tariq garden", "weight": "2.6", "points": "52"},
        {"date": "11/18/2024", "address": "54 H tariq garden", "weight": "3.5", "points": "62"},
        {"date": "10/07/2024", "address": "80 B block Tariq Garden", "weight": "4.9", "points": "100"},
        {"date": "10/07/2024", "address": "54 H tariq garden", "weight": "3.6", "points": "72"},
        {"date": "10/19/2024", "address": "54 A block Tariq garden", "weight": "3.7", "points": "74"},
        {"date": "10/28/2024", "address": "80 B block Tariq Garden", "weight": "8.5", "points": "172"},
        {"date": "10/31/2024", "address": "54 H tariq garden", "weight": "2.3", "points": "46"},
    ],
    "collection_data_2025": [
        {"date": "05.05.25", "address": "37 h tarik garden", "weight": "2", "points": "40"},
        {"date": "05.05.25", "address": "54 h tarik garden", "weight": "4.5", "points": "90"},
        {"date": "09.04.25", "address": "37 h tarik garden", "weight": "2", "points": "40"},
        {"date": "09.04.25", "address": "54 h tarik garden", "weight": "3.5", "points": "70"},
        {"date": "15.04.25", "address": "54h tarik garden", "weight": "2", "points": "40"},
        {"date": "15.04.25", "address": "37 h tarik garden", "weight": "3", "points": "60"},
        {"date": "15.04.25", "address": "46 h tarik garden", "weight": "3.2", "points": "64"},
        {"date": "05.02.25", "address": "54 h tarik garden", "weight": "4.2", "points": "84"},
        {"date": "05.02.25", "address": "46 h tarik garden", "weight": "2.2", "points": "44"},
        {"date": "05.02.25", "address": "80 b tarik garden", "weight": "7", "points": "140"},
    ],
    "total_collections": 20,
    "generated_at": "2024-12-19T10:30:00.000Z"
}