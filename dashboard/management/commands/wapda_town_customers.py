from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta, datetime
import random
import re
from difflib import SequenceMatcher
from accounts.models import CustomUser
from trash.models import TrashSubmission, CollectionRecord, RewardPointHistory

class Command(BaseCommand):
    help = 'Create demo data for Wapda Town customers with collection records'

    def handle(self, *args, **options):
        self.stdout.write('Creating Wapda Town customers with collection data...')
        
        # Create users
        self.create_wapda_town_users()
        
        # Create submissions and collection records from actual data
        self.create_wapda_town_collections_from_data()
        
        # Also create some random submissions for users without collection data
        self.create_wapda_town_submissions()
        self.create_wapda_town_collections()
        
        self.stdout.write(self.style.SUCCESS('Wapda Town customers and collection data created successfully!'))

    def create_wapda_town_users(self):
        """Create Wapda Town customers as users"""
        wapda_town_customers = [
            {"name": "M Zahid Ali", "address": "220 K grid station H2 block wapda town", "phone": "3218098027"},
            {"name": "Zaid Mehmood", "address": "275 J3 wapda town", "phone": "3234233330"},
            {"name": "Samia Yaqoob", "address": "581 G2 Wapda town lahore", "phone": "3214460813"},
            {"name": "Maqsood Ahmad", "address": "581 G2 Wapda town lahore", "phone": "3030454581"},
            {"name": "Durraiz Ahmad", "address": "65 H2 Wapda town", "phone": "3129448897"},
            {"name": "Qaisar Butt", "address": "112 H4 wapda town", "phone": "3228040178"},
            {"name": "Muhammad Azam", "address": "147 H4 Wapda town", "phone": "3014459829"},
            {"name": "Hamza Aasim", "address": "267 J2 wapda town", "phone": "3222284949"},
            {"name": "Abdul Hameed Amir", "address": "204 K3 wapda town", "phone": "3098994093"},
            {"name": "Umer Shamim", "address": "122 street 8 K2 block wapda town", "phone": "3354403446"},
            {"name": "Zafar", "address": "62 A1 block wapda town", "phone": "3334244770"},
            {"name": "Fahad Jamshed", "address": "74 A1 Wapda town", "phone": "3334176638"},
            {"name": "M Maaz", "address": "49 H2 Wapda town", "phone": "3361177700"},
            {"name": "Adnan Rauf", "address": "168 F2 Wapda town", "phone": "3004550228"},
            {"name": "Iqbal", "address": "82 F2 wapda town", "phone": "3230426864"},
            {"name": "M Shakeel Riffat", "address": "69 J2 Wapda town", "phone": "3009411401"},
            {"name": "Usman Ahmed", "address": "18 J3 Wapda town", "phone": "3078726699"},
            {"name": "Riaz Ahmed", "address": "77 F2 wapda town", "phone": "3238489080"},
            {"name": "M Umer", "address": "401 G4 wapda town", "phone": "3007540236"},
            {"name": "Talha Muneer", "address": "391 G4 Wapda town", "phone": "3336907624"},
            {"name": "Sohail Akbar", "address": "86 F2 Wapda town", "phone": "3274944873"},
            {"name": "Syed ul Rehman", "address": "141 G2 wapda town", "phone": "3004879413"},
            {"name": "Zeeshan", "address": "145 G2 wapda town", "phone": "3314027169"},
            {"name": "Zulfiqar Ali", "address": "77 A1 wapda town", "phone": "3224111681"},
            {"name": "M Ahmed", "address": "21 A1 wapda town", "phone": ""},
            {"name": "Rehan Majeed", "address": "110 A2 wapda town", "phone": "3214514880"},
            {"name": "Arif", "address": "11 A2 wapda town", "phone": "3310065266"},
            {"name": "Absara", "address": "8 A1 wapda town", "phone": "3009477927"},
            {"name": "Ismail", "address": "262 K3 wapda town", "phone": "3234720688"},
            {"name": "Abrar", "address": "263 K3 wapda town", "phone": "3214113535"},
            {"name": "Anjum", "address": "264 K3 wapda town", "phone": "3013052398"},
            {"name": "Raheel", "address": "264 K3 wapda town", "phone": "3219666623"},
            {"name": "khyzer yaqoob", "address": "273 K3 wapda town", "phone": "3324434470"},
            {"name": "Satain bilal", "address": "109 K3 wapda town", "phone": "3321641330"},
            {"name": "Mida Ali", "address": "240 K3 wapda town", "phone": "3094102498"},
            {"name": "ch Muhammad pervaiz", "address": "52 G5 wapda town", "phone": ""},
            {"name": "Mrs Abdul samad", "address": "50 G5 wapda town", "phone": "3074282755"},
            {"name": "Shoab younas", "address": "137 G5 wapda town", "phone": ""},
            {"name": "sobia", "address": "235 K2 wapda town ground floor", "phone": "3009435022"},
            {"name": "mrs Ahmad", "address": "235 K2 wapda town upper floor", "phone": "3234293381"},
            {"name": "ch muhammad", "address": "304 K3 wapda town", "phone": "3214245828"},
            {"name": "khrar hayat", "address": "304/A K3 wapda town upper portion", "phone": "3214258828"},
            {"name": "muhammad azam", "address": "229 K2 wapda town", "phone": "3214593569"},
            {"name": "mudasir", "address": "87 F 2 wapda town", "phone": "3203947330"},
            {"name": "Salman Shakeel", "address": "765 F2 wapda town", "phone": "3156146554"},
            {"name": "waleed javed", "address": "758 F2 wapda town", "phone": "3464686082"},
            {"name": "Abdullah", "address": "750 F2 wapda town", "phone": "3174930872"},
            {"name": "Msnayyar shuja", "address": "746 F2 wapda town", "phone": "3310481851"},
            {"name": "Ali khan", "address": "746 F wapda town upper floor", "phone": "3310481851"},
            {"name": "iqram", "address": "270 J3 wapda town", "phone": "3006833625"},
            {"name": "Salman", "address": "77 J2 wapda town", "phone": "3098109674"},
            {"name": "Muhammad Ilyas", "address": "716 F2 wapda town", "phone": "3084550045"},
            {"name": "Ms Awais", "address": "589 E2 wapda town", "phone": "3164100709"},
            {"name": "Muhammad ijaz", "address": "590 E2 wapda town", "phone": "3334678133"},
            {"name": "Malik farhan", "address": "525 F2 wapda town", "phone": "3294238221"},
            {"name": "Asad ur Rehman Barry", "address": "17 block K1 wapda town", "phone": "3214840602"},
            {"name": "moiz barry", "address": "17 K1 wapda town", "phone": "3454094449"},
            {"name": "Mohid", "address": "697 F2 wapda town", "phone": "3213704728"},
            {"name": "Muhammad Adil", "address": "74 K3 wapda town", "phone": "3334661583"},
            {"name": "Sikander Hayat", "address": "304 K3 wapda town", "phone": "3214148141"},
            {"name": "Adnan mehmood", "address": "73 J3 wapda town", "phone": ""},
            {"name": "Sikander", "address": "81 J3 wapda town", "phone": ""},
            {"name": "Fasih ur Rehman", "address": "237 H4 wapda town", "phone": "3204617317"},
            {"name": "Muhammad Jameel", "address": "27 k2 wapda town", "phone": ""},
            {"name": "Muhammad Umer", "address": "104 K2 wapda town", "phone": "3224424408"},
        ]
        
        for customer in wapda_town_customers:
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

    def create_wapda_town_submissions(self):
        """Create trash submissions for Wapda Town customers"""
        # Get all Wapda Town users
        wapda_town_users = CustomUser.objects.filter(location__icontains='wapda town')
        
        for user in wapda_town_users:
            # Create 1-3 submissions per user
            num_submissions = random.randint(1, 3)
            
            for i in range(num_submissions):
                submission = TrashSubmission.objects.create(
                    user=user,
                    estimated_weight=random.uniform(2.0, 8.0),
                    status='collected',
                    created_at=timezone.now() - timedelta(days=random.randint(1, 30))
                )
                self.stdout.write(f'Created submission for {user.username}: {submission.estimated_weight}kg')

    def create_wapda_town_collections(self):
        """Create collection records for Wapda Town customers"""
        # Get all collected submissions
        submissions = TrashSubmission.objects.filter(status='collected', user__location__icontains='wapda town')
        
        for submission in submissions:
            # Create collection record
            collection = CollectionRecord.objects.create(
                submission=submission,
                rider=None,  # No rider assigned
                actual_trash_type='other',
                actual_weight=submission.estimated_weight + random.uniform(-0.5, 0.5),
                reward_points=int(submission.estimated_weight * 20),  # 20 points per kg
                collected_at=submission.created_at + timedelta(hours=random.randint(1, 24)),
                admin_verified=True
            )
            
            # Update user's reward points
            submission.user.reward_points += collection.reward_points
            submission.user.save()
            
            self.stdout.write(f'Created collection record for {submission.user.username}: {collection.actual_weight}kg, {collection.reward_points} points')

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
                if 'wapda town' in user_normalized and 'wapda town' in collection_normalized:
                    matches.append(collection)
            elif self.similarity(user_normalized, collection_normalized) > 0.7:
                matches.append(collection)
        
        return matches

    def create_wapda_town_collections_from_data(self):
        """Create collection records from actual collection data"""
        # Wapda Town collection data from 2024 and 2025 (sample of most relevant ones)
        collection_data_2024 = [
            {"date": "12/02/2024", "address": "804 k3 wapda town", "weight": "3.1", "points": "62"},
            {"date": "12/04/2024", "address": "110 A2 wapda town", "weight": "5.4", "points": "108"},
            {"date": "12/04/2024", "address": "262 k3 wapda town", "weight": "3.5", "points": "70"},
            {"date": "11/02/2024", "address": "82 F2 wapda town", "weight": "3.1", "points": "62"},
            {"date": "11/04/2024", "address": "421 J2 wapda town", "weight": "11.2", "points": "104"},
            {"date": "11/04/2024", "address": "62 A1 wapda town", "weight": "2", "points": "40"},
            {"date": "11/04/2024", "address": "204 K3 wapda town", "weight": "4.4", "points": "90"},
            {"date": "11/12/2024", "address": "301 J2 wapda town", "weight": "2.1", "points": "42"},
            {"date": "11/12/2024", "address": "77 F2 wapda town", "weight": "4.1", "points": "83"},
            {"date": "11/13/2024", "address": "135 G5 wapda town", "weight": "2.8", "points": "56"},
            {"date": "11/15/2024", "address": "145 G2 wapda town", "weight": "2.7", "points": "56"},
            {"date": "11/21/2024", "address": "112 H4 wapda town", "weight": "3.8", "points": "76"},
            {"date": "11/21/2024", "address": "118 H4 wapda town", "weight": "4.8", "points": "96"},
            {"date": "11/22/2024", "address": "82 F2 wapda town", "weight": "2.3", "points": "47"},
            {"date": "11/22/2024", "address": "421 J2 wapda town", "weight": "4.3", "points": "86"},
            {"date": "11/22/2024", "address": "60 A1 wapda town", "weight": "3.8", "points": "76"},
            {"date": "11/22/2024", "address": "74 A1 wapda town", "weight": "4.2", "points": "84"},
            {"date": "11/23/2024", "address": "62 A1 wapda town", "weight": "2.8", "points": "56"},
            {"date": "11/25/2024", "address": "110 A2 wapda town", "weight": "6.2", "points": "124"},
            {"date": "11/25/2024", "address": "147 H4 wapda town", "weight": "3.9", "points": "80"},
            {"date": "11/27/2024", "address": "135 G5 wapda town", "weight": "4.5", "points": "90"},
            {"date": "11/27/2024", "address": "273 K3 wapda town", "weight": "7.6", "points": "152"},
        ]
        
        collection_data_2025 = [
            {"date": "05.05.25", "address": "135g5wapda town", "weight": "4", "points": "80"},
            {"date": "05.05.25", "address": "109 k3 wapda town", "weight": "4.5", "points": "90"},
            {"date": "05.05.25", "address": "421j2 wapda town", "weight": "6", "points": "120"},
            {"date": "05.05.25", "address": "39 j2 wapda town", "weight": "3.2", "points": "64"},
            {"date": "05.05.25", "address": "349 g2 wapda town", "weight": "3.2", "points": "64"},
            {"date": "05.05.25", "address": "346g2 wapda", "weight": "3", "points": "60"},
            {"date": "05.05.25", "address": "162f2 wapda town", "weight": "2.9", "points": "58"},
            {"date": "05.05.25", "address": "590 e2 wapda town", "weight": "3.5", "points": "70"},
            {"date": "05.05.25", "address": "525f2 wapda town", "weight": "7", "points": "140"},
            {"date": "12.05.25", "address": "109 k2 wapda town", "weight": "4", "points": "80"},
            {"date": "12.05.25", "address": "73 j3 wapda town", "weight": "3", "points": "60"},
            {"date": "12.05.25", "address": "275 j3 wapda town", "weight": "4", "points": "80"},
            {"date": "12.05.25", "address": "81 j3 wapda town", "weight": "5", "points": "100"},
            {"date": "12.05.25", "address": "237h4 wapda town", "weight": "4", "points": "80"},
            {"date": "12.05.25", "address": "17 k1 wapda town upper floor", "weight": "4", "points": "80"},
            {"date": "12.05.25", "address": "17 k1 wapda town ground floor", "weight": "6", "points": "120"},
            {"date": "12.05.25", "address": "110 block a 1 wapda town", "weight": "4.2", "points": "84"},
        ]
        
        all_collection_data = collection_data_2024 + collection_data_2025
        
        # Get all Wapda Town users
        wapda_town_users = CustomUser.objects.filter(location__icontains='wapda town')
        
        for user in wapda_town_users:
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
                weight = float(collection.get('weight', 0)) if collection.get('weight') else random.uniform(2.0, 8.0)
                submission = TrashSubmission.objects.create(
                    user=user,
                    estimated_weight=weight,
                    status='collected',
                    created_at=collection_date
                )
                
                # Create collection record
                points = int(collection.get('points', 0)) if collection.get('points') else int(weight * 20)
                collection_record = CollectionRecord.objects.create(
                    submission=submission,
                    rider=None,
                    actual_trash_type='other',
                    actual_weight=weight,
                    reward_points=points,
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
        {"date": "12/02/2024", "address": "804 k3 wapda town", "weight": "3.1", "points": "62"},
        {"date": "12/04/2024", "address": "110 A2 wapda town", "weight": "5.4", "points": "108"},
        {"date": "12/04/2024", "address": "262 k3 wapda town", "weight": "3.5", "points": "70"},
        {"date": "11/02/2024", "address": "82 F2 wapda town", "weight": "3.1", "points": "62"},
        {"date": "11/04/2024", "address": "421 J2 wapda town", "weight": "11.2", "points": "104"},
        {"date": "11/04/2024", "address": "62 A1 wapda town", "weight": "2", "points": "40"},
        {"date": "11/04/2024", "address": "204 K3 wapda town", "weight": "4.4", "points": "90"},
        {"date": "11/12/2024", "address": "301 J2 wapda town", "weight": "2.1", "points": "42"},
        {"date": "11/12/2024", "address": "77 F2 wapda town", "weight": "4.1", "points": "83"},
        {"date": "11/13/2024", "address": "135 G5 wapda town", "weight": "2.8", "points": "56"},
    ],
    "collection_data_2025": [
        {"date": "05.05.25", "address": "135g5wapda town", "weight": "4", "points": "80"},
        {"date": "05.05.25", "address": "109 k3 wapda town", "weight": "4.5", "points": "90"},
        {"date": "05.05.25", "address": "421j2 wapda town", "weight": "6", "points": "120"},
        {"date": "05.05.25", "address": "39 j2 wapda town", "weight": "3.2", "points": "64"},
        {"date": "05.05.25", "address": "349 g2 wapda town", "weight": "3.2", "points": "64"},
        {"date": "05.05.25", "address": "346g2 wapda", "weight": "3", "points": "60"},
        {"date": "05.05.25", "address": "162f2 wapda town", "weight": "2.9", "points": "58"},
        {"date": "05.05.25", "address": "590 e2 wapda town", "weight": "3.5", "points": "70"},
        {"date": "05.05.25", "address": "525f2 wapda town", "weight": "7", "points": "140"},
        {"date": "12.05.25", "address": "109 k2 wapda town", "weight": "4", "points": "80"},
    ],
    "total_collections": 20,
    "generated_at": "2024-12-19T10:30:00.000Z"
}