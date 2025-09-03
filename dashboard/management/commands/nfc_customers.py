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
    help = 'Create demo data for NFC customers with collection records'

    def handle(self, *args, **options):
        self.stdout.write('Creating NFC customers with collection data...')
        
        # Create users
        self.create_nfc_users()
        
        # Create submissions and collection records from actual data
        self.create_nfc_collections_from_data()
        
        # Also create some random submissions for users without collection data
        self.create_nfc_submissions()
        self.create_nfc_collections()
        
        self.stdout.write(self.style.SUCCESS('NFC customers and collection data created successfully!'))

    def create_nfc_users(self):
        """Create NFC customers as users"""
        nfc_customers = [
            {"name": "M Inam", "address": "9 D Street 7 NFC", "phone": "3334466911"},
            {"name": "Izhar Ahmed", "address": "plot no 45 C NFC", "phone": "3046096909"},
            {"name": "Khalid Shah", "address": "202 street 5 D block NFC", "phone": "3004699100"},
            {"name": "S M sadiq", "address": "126 D block Street 4 NFC", "phone": "3478084298"},
            {"name": "Ismael", "address": "155 Street 5 NFC", "phone": "3219029907"},
            {"name": "Ahtisham", "address": "10 D Block st 8 NFC", "phone": "3261301561"},
            {"name": "Khadija", "address": "24 D blockk street 4 NFC", "phone": "3084461571"},
            {"name": "Shm", "address": "11 D block NFC Street 9", "phone": "3278406364"},
            {"name": "Furqan", "address": "17 D Street 8 NFC society", "phone": "3340422639"},
            {"name": "Rashida", "address": "423 Street 5 D block NFC", "phone": "3233337135"},
            {"name": "Rehma Yousaf", "address": "438 Street 5 D block NFC", "phone": "3401605500"},
            {"name": "M Imran", "address": "6D street 3 NFC", "phone": "3016251905"},
            {"name": "Muhammad Asudullah", "address": "82 D block main street NFC", "phone": ""},
            {"name": "jamal raza", "address": "118 B2 street 2 NFC", "phone": "3224315291"},
            {"name": "Rao M Jalees", "address": "115 street 2 NFC", "phone": "3334101254"},
            {"name": "Zaheer ud din baber", "address": "101 street 1 B block NFC", "phone": "3004774594"},
            {"name": "Umair Majeed", "address": "109 D street 5 NFC", "phone": "3224002460"},
            {"name": "babar hassan", "address": "37 C 4th avenue NFC", "phone": "3014175016"},
            {"name": "waseem", "address": "115 7 ext bloock B NFC", "phone": "3035992117"},
            {"name": "naveed malik", "address": "114 street6 block B NFC", "phone": ""},
            {"name": "Asad kamal", "address": "132 B NFC street 6", "phone": "3184612413"},
            {"name": "Ayesha", "address": "127 B bloock street 6 NFC", "phone": ""},
            {"name": "Mrs Pervaiz", "address": "201 B Street 3 NFC", "phone": ""},
            {"name": "Munawar khan", "address": "101 street 7 block B NFC", "phone": "3314666240"},
            {"name": "Abdul majeed", "address": "307 B NFC", "phone": "3244161058"},
            {"name": "nimra", "address": "121 B street 6 NFC", "phone": ""},
            {"name": "Dr Jawed", "address": "13 B 8th strret NFC first floor", "phone": ""},
            {"name": "fawad yousaf", "address": "13 b 8th strret NFC second floor", "phone": ""},
            {"name": "Izhar", "address": "40 C street 8 NFC", "phone": "3011722884"},
        ]
        
        for customer in nfc_customers:
            # Create username from name
            username = customer["name"].lower().replace(" ", "_").replace(".", "")
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

    def create_nfc_submissions(self):
        """Create trash submissions for NFC customers"""
        # Get all NFC users
        nfc_users = CustomUser.objects.filter(location__icontains='NFC')
        
        for user in nfc_users:
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

    def create_nfc_collections(self):
        """Create collection records for NFC customers"""
        # Get all collected submissions
        submissions = TrashSubmission.objects.filter(status='collected', user__location__icontains='NFC')
        
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
                # Check if both contain NFC
                if 'nfc' in user_normalized and 'nfc' in collection_normalized:
                    matches.append(collection)
            # Also check for high similarity
            elif self.similarity(user_normalized, collection_normalized) > 0.7:
                matches.append(collection)
        
        return matches

    def create_nfc_collections_from_data(self):
        """Create collection records from actual collection data"""
        # Collection data from 2024 and 2025
        collection_data_2024 = [
            {"date": "12/02/2024", "address": "10 D street 8 NFC", "weight": "4", "points": "80"},
            {"date": "12/03/2024", "address": "17 D street 8 NFC", "weight": "2.2", "points": "44"},
            {"date": "11/12/2024", "address": "17 D street 8 NFC", "weight": "4.1", "points": "83"},
            {"date": "11/08/2024", "address": "155 D block street 5 NFC", "weight": "3.2", "points": "64"},
            {"date": "11/20/2024", "address": "155 D block street 5 NFC", "weight": "3.2", "points": "64"},
            {"date": "11/29/2024", "address": "155 D block street 5 NFC", "weight": "4.2", "points": "84"},
            {"date": "10/07/2024", "address": "NFC D block street 3", "weight": "1.9", "points": "38"},
            {"date": "10/09/2024", "address": "155 D block street 5 NFC", "weight": "3.7", "points": "74"},
            {"date": "10/15/2024", "address": "155 D block street 5 NFC", "weight": "3.4", "points": "69"},
            {"date": "10/18/2024", "address": "702 D street 4 NFC", "weight": "6.1", "points": "123"},
            {"date": "10/23/2024", "address": "155 D block street 5 NFC", "weight": "3.5", "points": "70"},
            {"date": "10/27/2024", "address": "155 D block street 5 NFC", "weight": "3.2", "points": "64"},
            {"date": "10/28/2024", "address": "808 D street 4 NFC", "weight": "6.3", "points": "127"},
            {"date": "09/06/2024", "address": "420 D street 1 NFC", "weight": "", "points": ""},
            {"date": "09/07/2024", "address": "155 D block street 5 NFC", "weight": "2.5", "points": "50"},
            {"date": "09/20/2024", "address": "703 D block street 4 NFC", "weight": "3.6", "points": "72"},
            {"date": "09/23/2024", "address": "155 D block street 5 NFC", "weight": "2.6", "points": "52"},
            {"date": "09/21/2024", "address": "street 9D block NFC", "weight": "2.1", "points": "42"},
        ]
        
        collection_data_2025 = [
            {"date": "07.05.25", "address": "126 b st 6 nfc", "weight": "2.5", "points": "50"},
            {"date": "09.05.25", "address": "307 b nfc", "weight": "5", "points": "100"},
            {"date": "11.04.25", "address": "132 b st 6 nfc", "weight": "3.2", "points": "64"},
            {"date": "11.04.25", "address": "8 st 8 d block nfc", "weight": "3.5", "points": "70"},
            {"date": "15.04.25", "address": "13 b nfc st 8", "weight": "3", "points": "60"},
            {"date": "15.04.25", "address": "423 b st 5 nfc", "weight": "3.4", "points": "68"},
            {"date": "15.04.25", "address": "126 b st6 nfc", "weight": "1.8", "points": "38"},
            {"date": "17.04.25", "address": "702 st.7 d block nfc", "weight": "3.2", "points": "64"},
            {"date": "17.04.25", "address": "164 st.6 b block nfc", "weight": "2.2", "points": "44"},
            {"date": "29.04.25", "address": "10 d st 5 nfc", "weight": "3", "points": "60"},
            {"date": "29.04.25", "address": "225 c st.8 nfc", "weight": "2.5", "points": "50"},
            {"date": "29.04.25", "address": "307 b nfc", "weight": "2.4", "points": "48"},
            {"date": "29.04.25", "address": "167 b st 6 nfc", "weight": "3", "points": "60"},
            {"date": "05.02.25", "address": "225c st 8 nfc", "weight": "2.2", "points": "44"},
            {"date": "05.02.25", "address": "307 b st 2 nfc", "weight": "3.4", "points": "68"},
            {"date": "05.02.25", "address": "13 b st 8 nfc", "weight": "3.2", "points": "64"},
            {"date": "20.02.25", "address": "37 c st 4 nfc", "weight": "3.2", "points": "64"},
            {"date": "20.02.25", "address": "202 st 5 d nfc", "weight": "2.7", "points": "54"},
            {"date": "28.02.25", "address": "82 d block main Street NFC", "weight": "3.2", "points": "64"},
            {"date": "28.02.25", "address": "155 d block Street 5 NFC", "weight": "3", "points": "60"},
            {"date": "28.02.25", "address": "115 b block st2 NFC", "weight": "1.8", "points": "36"},
            {"date": "31.01.25", "address": "155 d st.5 nfc", "weight": "3", "points": "60"},
            {"date": "31.01.25", "address": "225 c st 8 nfc", "weight": "2", "points": "40"},
            {"date": "31.01.25", "address": "10 d st 8 nfc", "weight": "3.2", "points": "64"},
            {"date": "29.01.25", "address": "82 d main street nfc", "weight": "3.4", "points": "68"},
            {"date": "29.01.25", "address": "101 st 1 b nfc", "weight": "2.5", "points": "50"},
        ]
        
        all_collection_data = collection_data_2024 + collection_data_2025
        
        # Get all NFC users
        nfc_users = CustomUser.objects.filter(location__icontains='NFC')
        
        for user in nfc_users:
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
        {"date": "12/02/2024", "address": "10 D street 8 NFC", "weight": "4", "points": "80"},
        {"date": "12/03/2024", "address": "17 D street 8 NFC", "weight": "2.2", "points": "44"},
        {"date": "11/12/2024", "address": "17 D street 8 NFC", "weight": "4.1", "points": "83"},
        {"date": "11/08/2024", "address": "155 D block street 5 NFC", "weight": "3.2", "points": "64"},
        {"date": "11/20/2024", "address": "155 D block street 5 NFC", "weight": "3.2", "points": "64"},
        {"date": "11/29/2024", "address": "155 D block street 5 NFC", "weight": "4.2", "points": "84"},
        {"date": "10/07/2024", "address": "NFC D block street 3", "weight": "1.9", "points": "38"},
        {"date": "10/09/2024", "address": "155 D block street 5 NFC", "weight": "3.7", "points": "74"},
        {"date": "10/15/2024", "address": "155 D block street 5 NFC", "weight": "3.4", "points": "69"},
        {"date": "10/18/2024", "address": "702 D street 4 NFC", "weight": "6.1", "points": "123"},
        {"date": "10/23/2024", "address": "155 D block street 5 NFC", "weight": "3.5", "points": "70"},
        {"date": "10/27/2024", "address": "155 D block street 5 NFC", "weight": "3.2", "points": "64"},
        {"date": "10/28/2024", "address": "808 D street 4 NFC", "weight": "6.3", "points": "127"},
        {"date": "09/06/2024", "address": "420 D street 1 NFC", "weight": "", "points": ""},
        {"date": "09/07/2024", "address": "155 D block street 5 NFC", "weight": "2.5", "points": "50"},
        {"date": "09/20/2024", "address": "703 D block street 4 NFC", "weight": "3.6", "points": "72"},
        {"date": "09/23/2024", "address": "155 D block street 5 NFC", "weight": "2.6", "points": "52"},
        {"date": "09/21/2024", "address": "street 9D block NFC", "weight": "2.1", "points": "42"},
    ],
    "collection_data_2025": [
        {"date": "07.05.25", "address": "126 b st 6 nfc", "weight": "2.5", "points": "50"},
        {"date": "09.05.25", "address": "307 b nfc", "weight": "5", "points": "100"},
        {"date": "11.04.25", "address": "132 b st 6 nfc", "weight": "3.2", "points": "64"},
        {"date": "11.04.25", "address": "8 st 8 d block nfc", "weight": "3.5", "points": "70"},
        {"date": "15.04.25", "address": "13 b nfc st 8", "weight": "3", "points": "60"},
        {"date": "15.04.25", "address": "423 b st 5 nfc", "weight": "3.4", "points": "68"},
        {"date": "15.04.25", "address": "126 b st6 nfc", "weight": "1.8", "points": "38"},
        {"date": "17.04.25", "address": "702 st.7 d block nfc", "weight": "3.2", "points": "64"},
        {"date": "17.04.25", "address": "164 st.6 b block nfc", "weight": "2.2", "points": "44"},
        {"date": "29.04.25", "address": "10 d st 5 nfc", "weight": "3", "points": "60"},
        {"date": "29.04.25", "address": "225 c st.8 nfc", "weight": "2.5", "points": "50"},
        {"date": "29.04.25", "address": "307 b nfc", "weight": "2.4", "points": "48"},
        {"date": "29.04.25", "address": "167 b st 6 nfc", "weight": "3", "points": "60"},
        {"date": "05.02.25", "address": "225c st 8 nfc", "weight": "2.2", "points": "44"},
        {"date": "05.02.25", "address": "307 b st 2 nfc", "weight": "3.4", "points": "68"},
        {"date": "05.02.25", "address": "13 b st 8 nfc", "weight": "3.2", "points": "64"},
        {"date": "20.02.25", "address": "37 c st 4 nfc", "weight": "3.2", "points": "64"},
        {"date": "20.02.25", "address": "202 st 5 d nfc", "weight": "2.7", "points": "54"},
        {"date": "28.02.25", "address": "82 d block main Street NFC", "weight": "3.2", "points": "64"},
        {"date": "28.02.25", "address": "155 d block Street 5 NFC", "weight": "3", "points": "60"},
        {"date": "28.02.25", "address": "115 b block st2 NFC", "weight": "1.8", "points": "36"},
        {"date": "31.01.25", "address": "155 d st.5 nfc", "weight": "3", "points": "60"},
        {"date": "31.01.25", "address": "225 c st 8 nfc", "weight": "2", "points": "40"},
        {"date": "31.01.25", "address": "10 d st 8 nfc", "weight": "3.2", "points": "64"},
        {"date": "29.01.25", "address": "82 d main street nfc", "weight": "3.4", "points": "68"},
        {"date": "29.01.25", "address": "101 st 1 b nfc", "weight": "2.5", "points": "50"},
    ],
    "total_collections": 43,
    "generated_at": "2024-12-19T10:30:00.000Z"
}