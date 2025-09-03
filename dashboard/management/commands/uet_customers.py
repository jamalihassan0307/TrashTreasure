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
    help = 'Create demo data for UET customers with collection records'

    def handle(self, *args, **options):
        self.stdout.write('Creating UET customers with collection data...')
        
        # Create users
        self.create_uet_users()
        
        # Create submissions and collection records from actual data
        self.create_uet_collections_from_data()
        
        # Also create some random submissions for users without collection data
        self.create_uet_submissions()
        self.create_uet_collections()
        
        self.stdout.write(self.style.SUCCESS('UET customers and collection data created successfully!'))

    def create_uet_users(self):
        """Create UET customers as users"""
        uet_customers = [
            {"name": "Sufyan", "address": "204 A UET housing society", "phone": "3344123683"},
            {"name": "Danish", "address": "6 B UET society", "phone": "3144229006"},
            {"name": "M Taha Akram", "address": "31 B UET society", "phone": "3214282347"},
            {"name": "MrsWaheed", "address": "162 B UET society", "phone": "3249631947"},
            {"name": "M Rafiq", "address": "208 B UET society", "phone": "3057885777"},
            {"name": "Shahzad Bukhari", "address": "B block UET Society", "phone": "3008520336"},
            {"name": "Uzaifa", "address": "308 B UET society", "phone": "3214050529"},
            {"name": "Moaz Muneer", "address": "123 B UET society", "phone": "3090030026"},
            {"name": "Haroon Ali", "address": "118 B UET society", "phone": "3074070167"},
            {"name": "Riaz Ahmed", "address": "57 C block UET society", "phone": "3029359953"},
            {"name": "Sidiqi", "address": "108 B UET society", "phone": ""},
            {"name": "Syed Anas Samdani", "address": "101 B block UET society", "phone": "3029566668"},
            {"name": "Dr Wajahat Ali", "address": "55 B UET society", "phone": "3234996276"},
            {"name": "Dr Azan", "address": "178 B UET society", "phone": "3214557151"},
            {"name": "Salman khan", "address": "329 Block C UET society", "phone": "3004239075"},
            {"name": "Syed Atiq", "address": "98/1 A UET society", "phone": "3218446448"},
            {"name": "Zahid Sadiqi", "address": "108 B UET society", "phone": "3224719575"},
            {"name": "Shakeel Ahmad", "address": "22 B UET", "phone": "3004599424"},
            {"name": "Masood Ahmed", "address": "150 B UET", "phone": "3334537046"},
            {"name": "Ahmad Munir", "address": "73 A UET", "phone": "3344110603"},
            {"name": "M Nasir", "address": "47 B UET", "phone": "3214495882"},
            {"name": "Mrs Taha", "address": "121/A block UET", "phone": "3315043789"},
            {"name": "Mirza zaffar", "address": "167 C block UET", "phone": "3344807394"},
            {"name": "mohsin", "address": "76 C uet", "phone": "3228091866"},
            {"name": "Tanveer basharat", "address": "78 C block UET", "phone": "3214086700"},
            {"name": "shehreen", "address": "143 B UET society", "phone": "3006963018"},
            {"name": "Saira", "address": "168 A UET", "phone": ""},
            {"name": "Zahid", "address": "310 C block UET", "phone": "3062699268"},
        ]
        
        for customer in uet_customers:
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

    def create_uet_submissions(self):
        """Create trash submissions for UET customers"""
        # Get all UET users
        uet_users = CustomUser.objects.filter(location__icontains='UET')
        
        for user in uet_users:
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

    def create_uet_collections(self):
        """Create collection records for UET customers"""
        # Get all collected submissions
        submissions = TrashSubmission.objects.filter(status='collected', user__location__icontains='UET')
        
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
        # Look for numbers at the beginning of the address
        match = re.match(r'^(\d+)', address.strip())
        if match:
            return match.group(1)
        return None

    def normalize_address(self, address):
        """Normalize address for better matching"""
        if not address:
            return ""
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', address.lower().strip())
        # Remove common variations
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
            
            # Check if house numbers match
            if user_house_num and collection_house_num and user_house_num == collection_house_num:
                # Check if both contain UET
                if 'uet' in user_normalized and 'uet' in collection_normalized:
                    matches.append(collection)
            # Also check for high similarity
            elif self.similarity(user_normalized, collection_normalized) > 0.7:
                matches.append(collection)
        
        return matches

    def create_uet_collections_from_data(self):
        """Create collection records from actual collection data"""
        # Collection data from 2024 and 2025 for UET
        collection_data_2024 = [
            {"date": "12/03/2024", "address": "329 C block UET", "weight": "5", "points": "100"},
            {"date": "12/05/2024", "address": "108 B UET society", "weight": "5.6", "points": "112"},
            {"date": "12/05/2024", "address": "223 B UET society", "weight": "4.8", "points": "96"},
            {"date": "12/05/2024", "address": "178 B UET society", "weight": "4.3", "points": "86"},
            {"date": "12/05/2024", "address": "73 A UET society", "weight": "2", "points": "40"},
            {"date": "12/05/2024", "address": "98/1 A UET society", "weight": "5.6", "points": "112"},
            {"date": "11/05/2024", "address": "6 B UET", "weight": "5.9", "points": "120"},
            {"date": "11/05/2024", "address": "29/A B block UET", "weight": "3.7", "points": "75"},
            {"date": "11/20/2024", "address": "66/A UET", "weight": "4.2", "points": "84"},
            {"date": "11/20/2024", "address": "129/A UET", "weight": "2.6", "points": "52"},
            {"date": "11/20/2024", "address": "162 B UET", "weight": "3.4", "points": "68"},
            {"date": "11/25/2024", "address": "175 B UET", "weight": "3.1", "points": "62"},
            {"date": "11/26/2024", "address": "29/A B block UET", "weight": "3", "points": "60"},
            {"date": "11/26/2024", "address": "110 Block A UET", "weight": "4", "points": "80"},
            {"date": "11/27/2024", "address": "308 A B UET", "weight": "3.2", "points": "64"},
            {"date": "10/04/2024", "address": "51 A UET society", "weight": "3.3", "points": "67"},
            {"date": "10/04/2024", "address": "31 B UET society", "weight": "3.2", "points": "64"},
            {"date": "10/09/2024", "address": "121/A UET society", "weight": "1.8", "points": "36"},
            {"date": "10/09/2024", "address": "162 B UET society", "weight": "4.5", "points": "90"},
            {"date": "10/10/2024", "address": "6 B UET society", "weight": "3.3", "points": "67"},
            {"date": "10/14/2024", "address": "31 B UET society", "weight": "3.2", "points": "65"},
            {"date": "10/14/2024", "address": "51 A UET society", "weight": "1.9", "points": "38"},
            {"date": "10/16/2024", "address": "29 B block UET", "weight": "5.1", "points": "104"},
            {"date": "10/16/2024", "address": "308 A block UET", "weight": "1.9", "points": "40"},
            {"date": "10/18/2024", "address": "175 B UET", "weight": "2.7", "points": "56"},
            {"date": "10/30/2024", "address": "162 B block UET", "weight": "2.6", "points": "52"},
            {"date": "10/30/2024", "address": "175 B UET", "weight": "4", "points": "80"},
            {"date": "09/11/2024", "address": "55 A UET society", "weight": "2.5", "points": "50"},
            {"date": "09/23/2024", "address": "147 A block UET", "weight": "2.3", "points": "46"},
            {"date": "09/23/2024", "address": "31 B UET society", "weight": "3.5", "points": "70"},
            {"date": "09/24/2024", "address": "29/1 B block", "weight": "5.5", "points": "110"},
            {"date": "09/24/2024", "address": "29/1 A B block UET", "weight": "5.5", "points": "110"},
            {"date": "09/24/2024", "address": "51/A UET", "weight": "2.3", "points": "46"},
            {"date": "09/25/2024", "address": "66 A block UET society", "weight": "5.4", "points": "108"},
        ]
        
        collection_data_2025 = [
            {"date": "02.05.25", "address": "98 A Uet", "weight": "2", "points": "40"},
            {"date": "20525", "address": "118 b uet", "weight": "2.5", "points": "50"},
            {"date": "05.05.25", "address": "29 a b uet", "weight": "2", "points": "40"},
            {"date": "05.05.25", "address": "110 block a uet", "weight": "4.5", "points": "90"},
            {"date": "09.05.25", "address": "108 b uet", "weight": "3", "points": "60"},
            {"date": "09.05.25", "address": "329 c uet", "weight": "3", "points": "60"},
            {"date": "09.05.25", "address": "112 b uet", "weight": "3.2", "points": "64"},
            {"date": "12.05.25", "address": "162b uet", "weight": "3.5", "points": "70"},
            {"date": "6 b uet", "address": "12.05.25", "weight": "1.5", "points": "30"},
            {"date": "04.04.25", "address": "108 b uet 3.5", "weight": "3.5", "points": "70"},
            {"date": "04.04.25", "address": "66 a uet", "weight": "2.8", "points": "56"},
            {"date": "14 b uet", "address": "04.04.25", "weight": "2.9", "points": "58"},
            {"date": "11.04.25", "address": "29 b uet", "weight": "4", "points": "80"},
            {"date": "11.04.25", "address": "109 b uet", "weight": "3", "points": "60"},
            {"date": "11.04.25", "address": "121 a uet", "weight": "3", "points": "60"},
            {"date": "11.04.25", "address": "98 a uet", "weight": "1", "points": "20"},
            {"date": "11.04.25", "address": "110 a uet", "weight": "1.5", "points": "30"},
            {"date": "17.04.25", "address": "14 b uet", "weight": "5", "points": "100"},
            {"date": "22.04.25", "address": "308b Uet", "weight": "3", "points": "60"},
            {"date": "22.04.25", "address": "29a Uet", "weight": "2", "points": "40"},
            {"date": "23.04.25", "address": "110a Uet", "weight": "5.3", "points": "106"},
            {"date": "23.04.25", "address": "66a Uet", "weight": "5.5", "points": "110"},
            {"date": "03.02.25", "address": "168 A uet", "weight": "5.2", "points": "104"},
            {"date": "03.02.25", "address": "121 A uet", "weight": "3.1", "points": "62"},
            {"date": "03.02.25", "address": "98 a uet", "weight": "2", "points": "40"},
            {"date": "03.02.25", "address": "110 a uet", "weight": "3.1", "points": "62"},
            {"date": "03.02.25", "address": "6 b uet", "weight": "1.6", "points": "32"},
            {"date": "10.02.25", "address": "29 b uet", "weight": "7", "points": "140"},
            {"date": "10.02.25", "address": "150 b uet", "weight": "2.4", "points": "48"},
            {"date": "10.02.25", "address": "66/a uet", "weight": "4.2", "points": "84"},
            {"date": "12.02.25", "address": "268 b uet", "weight": "4.1", "points": "82"},
            {"date": "14.02.25", "address": "162 b uet", "weight": "2.4", "points": "48"},
            {"date": "14.02.25", "address": "108 b uet", "weight": "4.6", "points": "92"},
            {"date": "14.02.25", "address": "22 b uet", "weight": "2.2", "points": "44"},
            {"date": "20.02.25", "address": "168 a uet", "weight": "3", "points": "60"},
            {"date": "17.02.25", "address": "73 a uet", "weight": "3.6", "points": "72"},
            {"date": "25.02.25", "address": "47 b b u e t", "weight": "2.2", "points": "44"},
            {"date": "25.02.25", "address": "6 b uet", "weight": "5.2", "points": "104"},
            {"date": "16.01.25", "address": "40 c uet", "weight": "5.8", "points": "116"},
            {"date": "21.01.25", "address": "329 c uet", "weight": "4.8", "points": "96"},
            {"date": "21.01.25", "address": "208 b uet", "weight": "3.8", "points": "76"},
            {"date": "21 .01.25", "address": "308 b uet", "weight": "2.8", "points": "56"},
            {"date": "21.01.25", "address": "14 b uet", "weight": "2.4", "points": "48"},
            {"date": "24.01.25", "address": "47 b uet", "weight": "2.6", "points": "52"},
            {"date": "24.01.25", "address": "40 c uet", "weight": "2.4", "points": "48"},
            {"date": "27.01.25", "address": "40 c uet", "weight": "2.2", "points": "44"},
        ]
        
        all_collection_data = collection_data_2024 + collection_data_2025
        
        # Get all UET users
        uet_users = CustomUser.objects.filter(location__icontains='UET')
        
        for user in uet_users:
            # Find matching collections for this user
            matching_collections = self.find_matching_collections(user.location, all_collection_data)
            
            for collection in matching_collections:
                # Parse date
                try:
                    if '/' in collection['date']:
                        if len(collection['date'].split('/')) == 3:
                            if collection['date'].count('/') == 2:
                                # Format: MM/DD/YYYY or DD/MM/YYYY
                                date_parts = collection['date'].split('/')
                                if len(date_parts[2]) == 4:  # YYYY format
                                    if int(date_parts[0]) > 12:  # DD/MM/YYYY
                                        collection_date = datetime.strptime(collection['date'], '%d/%m/%Y')
                                    else:  # MM/DD/YYYY
                                        collection_date = datetime.strptime(collection['date'], '%m/%d/%Y')
                                else:  # YY format
                                    if int(date_parts[0]) > 12:  # DD/MM/YY
                                        collection_date = datetime.strptime(collection['date'], '%d/%m/%y')
                                    else:  # MM/DD/YY
                                        collection_date = datetime.strptime(collection['date'], '%m/%d/%y')
                            else:
                                collection_date = datetime.strptime(collection['date'], '%d/%m/%y')
                        else:
                            collection_date = datetime.strptime(collection['date'], '%d/%m/%y')
                    else:
                        # Format: DD.MM.YY
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
        {"date": "12/03/2024", "address": "329 C block UET", "weight": "5", "points": "100"},
        {"date": "12/05/2024", "address": "108 B UET society", "weight": "5.6", "points": "112"},
        {"date": "12/05/2024", "address": "223 B UET society", "weight": "4.8", "points": "96"},
        {"date": "12/05/2024", "address": "178 B UET society", "weight": "4.3", "points": "86"},
        {"date": "12/05/2024", "address": "73 A UET society", "weight": "2", "points": "40"},
        {"date": "12/05/2024", "address": "98/1 A UET society", "weight": "5.6", "points": "112"},
        {"date": "11/05/2024", "address": "6 B UET", "weight": "5.9", "points": "120"},
        {"date": "11/05/2024", "address": "29/A B block UET", "weight": "3.7", "points": "75"},
        {"date": "11/20/2024", "address": "66/A UET", "weight": "4.2", "points": "84"},
        {"date": "11/20/2024", "address": "129/A UET", "weight": "2.6", "points": "52"},
        {"date": "11/20/2024", "address": "162 B UET", "weight": "3.4", "points": "68"},
        {"date": "11/25/2024", "address": "175 B UET", "weight": "3.1", "points": "62"},
        {"date": "11/26/2024", "address": "29/A B block UET", "weight": "3", "points": "60"},
        {"date": "11/26/2024", "address": "110 Block A UET", "weight": "4", "points": "80"},
        {"date": "11/27/2024", "address": "308 A B UET", "weight": "3.2", "points": "64"},
        {"date": "10/04/2024", "address": "51 A UET society", "weight": "3.3", "points": "67"},
        {"date": "10/04/2024", "address": "31 B UET society", "weight": "3.2", "points": "64"},
        {"date": "10/09/2024", "address": "121/A UET society", "weight": "1.8", "points": "36"},
        {"date": "10/09/2024", "address": "162 B UET society", "weight": "4.5", "points": "90"},
        {"date": "10/10/2024", "address": "6 B UET society", "weight": "3.3", "points": "67"},
        {"date": "10/14/2024", "address": "31 B UET society", "weight": "3.2", "points": "65"},
        {"date": "10/14/2024", "address": "51 A UET society", "weight": "1.9", "points": "38"},
        {"date": "10/16/2024", "address": "29 B block UET", "weight": "5.1", "points": "104"},
        {"date": "10/16/2024", "address": "308 A block UET", "weight": "1.9", "points": "40"},
        {"date": "10/18/2024", "address": "175 B UET", "weight": "2.7", "points": "56"},
        {"date": "10/30/2024", "address": "162 B block UET", "weight": "2.6", "points": "52"},
        {"date": "10/30/2024", "address": "175 B UET", "weight": "4", "points": "80"},
        {"date": "09/11/2024", "address": "55 A UET society", "weight": "2.5", "points": "50"},
        {"date": "09/23/2024", "address": "147 A block UET", "weight": "2.3", "points": "46"},
        {"date": "09/23/2024", "address": "31 B UET society", "weight": "3.5", "points": "70"},
        {"date": "09/24/2024", "address": "29/1 B block", "weight": "5.5", "points": "110"},
        {"date": "09/24/2024", "address": "29/1 A B block UET", "weight": "5.5", "points": "110"},
        {"date": "09/24/2024", "address": "51/A UET", "weight": "2.3", "points": "46"},
        {"date": "09/25/2024", "address": "66 A block UET society", "weight": "5.4", "points": "108"},
    ],
    "collection_data_2025": [
        {"date": "02.05.25", "address": "98 A Uet", "weight": "2", "points": "40"},
        {"date": "20525", "address": "118 b uet", "weight": "2.5", "points": "50"},
        {"date": "05.05.25", "address": "29 a b uet", "weight": "2", "points": "40"},
        {"date": "05.05.25", "address": "110 block a uet", "weight": "4.5", "points": "90"},
        {"date": "09.05.25", "address": "108 b uet", "weight": "3", "points": "60"},
        {"date": "09.05.25", "address": "329 c uet", "weight": "3", "points": "60"},
        {"date": "09.05.25", "address": "112 b uet", "weight": "3.2", "points": "64"},
        {"date": "12.05.25", "address": "162b uet", "weight": "3.5", "points": "70"},
        {"date": "6 b uet", "address": "12.05.25", "weight": "1.5", "points": "30"},
        {"date": "04.04.25", "address": "108 b uet 3.5", "weight": "3.5", "points": "70"},
        {"date": "04.04.25", "address": "66 a uet", "weight": "2.8", "points": "56"},
        {"date": "14 b uet", "address": "04.04.25", "weight": "2.9", "points": "58"},
        {"date": "11.04.25", "address": "29 b uet", "weight": "4", "points": "80"},
        {"date": "11.04.25", "address": "109 b uet", "weight": "3", "points": "60"},
        {"date": "11.04.25", "address": "121 a uet", "weight": "3", "points": "60"},
        {"date": "11.04.25", "address": "98 a uet", "weight": "1", "points": "20"},
        {"date": "11.04.25", "address": "110 a uet", "weight": "1.5", "points": "30"},
        {"date": "17.04.25", "address": "14 b uet", "weight": "5", "points": "100"},
        {"date": "22.04.25", "address": "308b Uet", "weight": "3", "points": "60"},
        {"date": "22.04.25", "address": "29a Uet", "weight": "2", "points": "40"},
        {"date": "23.04.25", "address": "110a Uet", "weight": "5.3", "points": "106"},
        {"date": "23.04.25", "address": "66a Uet", "weight": "5.5", "points": "110"},
        {"date": "03.02.25", "address": "168 A uet", "weight": "5.2", "points": "104"},
        {"date": "03.02.25", "address": "121 A uet", "weight": "3.1", "points": "62"},
        {"date": "03.02.25", "address": "98 a uet", "weight": "2", "points": "40"},
        {"date": "03.02.25", "address": "110 a uet", "weight": "3.1", "points": "62"},
        {"date": "03.02.25", "address": "6 b uet", "weight": "1.6", "points": "32"},
        {"date": "10.02.25", "address": "29 b uet", "weight": "7", "points": "140"},
        {"date": "10.02.25", "address": "150 b uet", "weight": "2.4", "points": "48"},
        {"date": "10.02.25", "address": "66/a uet", "weight": "4.2", "points": "84"},
        {"date": "12.02.25", "address": "268 b uet", "weight": "4.1", "points": "82"},
        {"date": "14.02.25", "address": "162 b uet", "weight": "2.4", "points": "48"},
        {"date": "14.02.25", "address": "108 b uet", "weight": "4.6", "points": "92"},
        {"date": "14.02.25", "address": "22 b uet", "weight": "2.2", "points": "44"},
        {"date": "20.02.25", "address": "168 a uet", "weight": "3", "points": "60"},
        {"date": "17.02.25", "address": "73 a uet", "weight": "3.6", "points": "72"},
        {"date": "25.02.25", "address": "47 b b u e t", "weight": "2.2", "points": "44"},
        {"date": "25.02.25", "address": "6 b uet", "weight": "5.2", "points": "104"},
        {"date": "16.01.25", "address": "40 c uet", "weight": "5.8", "points": "116"},
        {"date": "21.01.25", "address": "329 c uet", "weight": "4.8", "points": "96"},
        {"date": "21.01.25", "address": "208 b uet", "weight": "3.8", "points": "76"},
        {"date": "21 .01.25", "address": "308 b uet", "weight": "2.8", "points": "56"},
        {"date": "21.01.25", "address": "14 b uet", "weight": "2.4", "points": "48"},
        {"date": "24.01.25", "address": "47 b uet", "weight": "2.6", "points": "52"},
        {"date": "24.01.25", "address": "40 c uet", "weight": "2.4", "points": "48"},
        {"date": "27.01.25", "address": "40 c uet", "weight": "2.2", "points": "44"},
    ],
    "total_collections": 82,
    "generated_at": "2024-12-19T10:30:00.000Z"
}