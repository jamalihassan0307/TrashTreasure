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
    help = 'Create demo data for Valencia customers with collection records'

    def handle(self, *args, **options):
        self.stdout.write('Creating Valencia customers with collection data...')
        
        # Create users
        self.create_valencia_users()
        
        # Create submissions and collection records from actual data
        self.create_valencia_collections_from_data()
        
        # Also create some random submissions for users without collection data
        self.create_valencia_submissions()
        self.create_valencia_collections()
        
        self.stdout.write(self.style.SUCCESS('Valencia customers and collection data created successfully!'))

    def create_valencia_users(self):
        """Create Valencia customers as users"""
        valencia_customers = [
            {"name": "Muhammad Ayyub", "address": "111 E Valencia", "phone": "3004024088"},
            {"name": "M Qaisar", "address": "144 J1 Valencia", "phone": "3218482748"},
            {"name": "Shahid Iqbal", "address": "202 A1 Valencia", "phone": "3004933226"},
            {"name": "Husnain Aslam", "address": "36 C1 Valencia", "phone": "3346614555"},
            {"name": "firdous Munir", "address": "41/A block C1 valencia", "phone": "3004411881"},
            {"name": "Fara Sajid", "address": "38 A block valencia", "phone": "3071011944"},
            {"name": "Dr Mumtaz Salik", "address": "101 A valencia", "phone": "3224340294"},
            {"name": "Maria Ali", "address": "100 Ablock Valencia", "phone": "3474718386"},
            {"name": "Jannat bibi", "address": "21 M block valencia", "phone": "3284817870"},
            {"name": "Niaz Ahmad", "address": "15 M block valencia", "phone": "3216504949"},
            {"name": "M Tahir Mahmood", "address": "12 M block valencia", "phone": "3244727973"},
            {"name": "Ali Raza Khan", "address": "75 F2 Block Valencia", "phone": "3018411006"},
            {"name": "Naveed Aftab", "address": "84 F block Valencia", "phone": "3008415825"},
            {"name": "Fakhar u Zaman", "address": "98 C block Valencia", "phone": "3240506303"},
            {"name": "Muhammad Tariq", "address": "56 J block Valencia", "phone": "3347300216"},
            {"name": "Tahwar Inshal", "address": "82 Cblock valencia", "phone": "3410473088"},
            {"name": "Inayat Ul Allah", "address": "190 E block Valencia", "phone": "3027699334"},
            {"name": "Tariq Mehmood", "address": "35 A1 block Valencia", "phone": "3006963018"},
            {"name": "Muhammad Abbas", "address": "78 C block Valencia", "phone": "3026424524"},
            {"name": "Umer", "address": "120 C block Valencia", "phone": "3097888827"},
            {"name": "Diyyal Nouman", "address": "166 A block Valencia", "phone": "3008458486"},
            {"name": "Shaheer", "address": "30 C1 Valencia", "phone": "3457044044"},
            {"name": "M Hassan", "address": "125 C block valencia", "phone": "3334107055"},
            {"name": "M Usman", "address": "68 A3 Valencia", "phone": "3035408863"},
            {"name": "Khadija", "address": "105 C block Valencia", "phone": "3004904616"},
            {"name": "Anjum", "address": "246 A valencia E block", "phone": ""},
            {"name": "Fahad Amjad", "address": "27 A1 valencia", "phone": "3004013747"},
            {"name": "Salawat Ahmed", "address": "216 A1 valencia", "phone": "3008414700"},
            {"name": "Jawad Ahmed", "address": "138 A valencia", "phone": "3334737627"},
            {"name": "Ahsan", "address": "80 C valencia", "phone": "3008429501"},
            {"name": "Muhammad Riaz", "address": "110 E 1 Valencia town", "phone": "3215456836"},
            {"name": "Rao Qaisar", "address": "132 E1 valencia", "phone": "3044500089"},
            {"name": "Faisal", "address": "110 A2 valencia", "phone": "3009443389"},
            {"name": "Hamza Shahzad", "address": "40 J1 valencia", "phone": "3218490448"},
            {"name": "Dr Sabir Ali", "address": "330 J block valencia", "phone": ""},
            {"name": "Ibsar", "address": "72 C block valencia", "phone": "3316414778"},
            {"name": "Mubeen irfan", "address": "109 C block valencia", "phone": "3218491113"},
            {"name": "Shabir Rana", "address": "124 J block valencia", "phone": "3214824608"},
            {"name": "Muhammad Ali", "address": "87 C valencia", "phone": ""},
            {"name": "Yasir Hayat", "address": "108 T block valencia", "phone": "3214666020"},
            {"name": "Zaki cheema", "address": "95 E valencia", "phone": "3370481931"},
            {"name": "Dr Arif", "address": "102 E1 valencia", "phone": "3333182790"},
            {"name": "Abdul Wahab", "address": "18 E block valencia", "phone": "3233666236"},
            {"name": "Najeeb Ahmed", "address": "125 E valencia", "phone": "3214243597"},
            {"name": "Qari M. Shafiq ur Rehman", "address": "133 E valencia", "phone": "3022100003"},
            {"name": "Madeem Akhter", "address": "108 A2 valencia", "phone": "3208441112"},
            {"name": "Ghulam Hussain", "address": "127 A2 valencia", "phone": "3045099531"},
            {"name": "Zahid Hameed", "address": "4 L valencia", "phone": "3018666298"},
            {"name": "Asad Kareem", "address": "125 A2 valencia", "phone": "3004362005"},
            {"name": "Farah taimoor", "address": "275 A1 valencia", "phone": ""},
            {"name": "shehzad", "address": "39 A1 valencia", "phone": "3370438015"},
            {"name": "shehzad ahmad", "address": "86 A1 Valencia", "phone": "3227666755"},
            {"name": "Ibad Jammal", "address": "17 E1 valencia", "phone": "3004004405"},
        ]
        
        for customer in valencia_customers:
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

    def create_valencia_submissions(self):
        """Create trash submissions for Valencia customers"""
        # Get all Valencia users
        valencia_users = CustomUser.objects.filter(location__icontains='valencia')
        
        for user in valencia_users:
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

    def create_valencia_collections(self):
        """Create collection records for Valencia customers"""
        # Get all collected submissions
        submissions = TrashSubmission.objects.filter(status='collected', user__location__icontains='valencia')
        
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
                if 'valencia' in user_normalized and 'valencia' in collection_normalized:
                    matches.append(collection)
            elif self.similarity(user_normalized, collection_normalized) > 0.7:
                matches.append(collection)
        
        return matches

    def create_valencia_collections_from_data(self):
        """Create collection records from actual collection data"""
        # Valencia collection data from 2024 and 2025
        collection_data_2024 = [
            {"date": "12/02/2024", "address": "14 A3 valencia", "weight": "2.4", "points": "48"},
            {"date": "12/03/2024", "address": "71 M valencia", "weight": "2.2", "points": "44"},
            {"date": "12/03/2024", "address": "182 A1 valencia", "weight": "3.2", "points": "64"},
            {"date": "12/03/2024", "address": "27 A1 valencia", "weight": "5.5", "points": "110"},
            {"date": "12/03/2024", "address": "266/A E valencia", "weight": "4.2", "points": "84"},
            {"date": "12/03/2024", "address": "4 L valencia", "weight": "4.7", "points": "94"},
            {"date": "12/04/2024", "address": "111 E valencia", "weight": "4", "points": "80"},
            {"date": "12/04/2024", "address": "95 E valencia", "weight": "4.4", "points": "88"},
            {"date": "12/04/2024", "address": "98 C block valencia", "weight": "2.6", "points": "53"},
            {"date": "12/05/2024", "address": "276 B valencia", "weight": "3.8", "points": "80"},
            {"date": "11/01/2024", "address": "35 C1 Valencia", "weight": "2", "points": "40"},
            {"date": "11/01/2024", "address": "41 C1 valencia", "weight": "3.3", "points": "65"},
            {"date": "11/01/2024", "address": "121 E Valencia", "weight": "3.2", "points": "64"},
            {"date": "11/02/2024", "address": "82 C valencia", "weight": "3.3", "points": "66"},
            {"date": "11/04/2024", "address": "98 C block valencia", "weight": "3.2", "points": "65"},
            {"date": "11/04/2024", "address": "266/A E block valencia", "weight": "7.8", "points": "156"},
            {"date": "11/04/2024", "address": "119 C valencia", "weight": "7", "points": "143"},
            {"date": "11/04/2024", "address": "60 A1 valencia", "weight": "2.2", "points": "44"},
            {"date": "11/04/2024", "address": "18 E valencia", "weight": "3.2", "points": "64"},
            {"date": "11/05/2024", "address": "14 A3 valencia", "weight": "1.3", "points": "26"},
            {"date": "11/12/2024", "address": "95 E valencia", "weight": "5.2", "points": "104"},
            {"date": "11/13/2024", "address": "166 A block valencia", "weight": "2.9", "points": "58"},
            {"date": "11/13/2024", "address": "71 M block valencia", "weight": "4", "points": "80"},
            {"date": "11/13/2024", "address": "166 A block valencia", "weight": "2.6", "points": "52"},
            {"date": "11/15/2024", "address": "275 B valencia", "weight": "11", "points": "223"},
            {"date": "11/15/2024", "address": "27 A1 valencia", "weight": "10.2", "points": "240"},
            {"date": "11/15/2024", "address": "216 A block valencia", "weight": "6.2", "points": "124"},
            {"date": "11/15/2024", "address": "121 E Valencia", "weight": "1.9", "points": "38"},
            {"date": "11/15/2024", "address": "18 E valencia", "weight": "2.7", "points": "34"},
            {"date": "11/16/2024", "address": "56 J valencia", "weight": "2.7", "points": "54"},
            {"date": "11/16/2024", "address": "103 E1 valencia", "weight": "3.6", "points": "72"},
            {"date": "11/18/2024", "address": "95E valencia", "weight": "11.5", "points": "223"},
            {"date": "11/18/2024", "address": "75 C valencia", "weight": "12", "points": "240"},
            {"date": "11/18/2024", "address": "36 c1 valencia", "weight": "3.1", "points": "62"},
            {"date": "11/18/2024", "address": "98 C block valencia", "weight": "7", "points": "140"},
            {"date": "11/19/2024", "address": "80 E valencia", "weight": "3.8", "points": "76"},
            {"date": "11/20/2024", "address": "138/A valencia", "weight": "1.4", "points": "28"},
            {"date": "11/20/2024", "address": "111 E valencia", "weight": "4.4", "points": "88"},
            {"date": "11/22/2024", "address": "60 A1 valencia", "weight": "3.8", "points": "76"},
            {"date": "11/22/2024", "address": "105 c block valencia", "weight": "2.9", "points": "58"},
            {"date": "11/25/2024", "address": "266 E block valencia", "weight": "5.1", "points": "102"},
            {"date": "11/25/2024", "address": "41 C1 valencia", "weight": "4.8", "points": "96"},
            {"date": "11/28/2024", "address": "18 E valencia", "weight": "5.2", "points": "104"},
            {"date": "11/28/2024", "address": "127 A2 B block valencia", "weight": "4.2", "points": "84"},
            {"date": "11/28/2024", "address": "266 E block valencia", "weight": "3", "points": "60"},
            {"date": "11/29/2024", "address": "276 B valencia", "weight": "4.2", "points": "84"},
        ]
        
        collection_data_2025 = [
            {"date": "02.05.25", "address": "18 e valencia", "weight": "3.2", "points": "64"},
            {"date": "02.05.25", "address": "45j valencia", "weight": "3.3", "points": "66"},
            {"date": "05.05.25", "address": "95e valencia", "weight": "6", "points": "120"},
            {"date": "05.05.25", "address": "84 f valencia", "weight": "total points 372", "points": ""},
            {"date": "12.05.25", "address": "36 c1 valencia3.6", "weight": "3.6", "points": "72"},
            {"date": "12.05.25", "address": "98c valencia", "weight": "2.5", "points": "50"},
            {"date": "12.05.25", "address": "95 e valencia", "weight": "4", "points": "80"},
            {"date": "12.05.25", "address": "84 e valencia", "weight": "4.5+6", "points": "90+120"},
            {"date": "12.05.25", "address": "18e valencia", "weight": "3", "points": "60"},
            {"date": "07.04.25", "address": "95 e valencia", "weight": "7.7", "points": "154"},
            {"date": "09.04.25", "address": "j block Valencia", "weight": "1.2", "points": "24"},
            {"date": "09.04.25", "address": "216 a1 valencia", "weight": "2.4", "points": "48"},
            {"date": "09.04.25", "address": "110 e 2 Valencia", "weight": "3", "points": "60"},
            {"date": "09.04.25", "address": "80 e valencia", "weight": "5.4+2.1", "points": "150"},
            {"date": "09.04.25", "address": "84 f valencia", "weight": "2", "points": "40"},
            {"date": "09.04.25", "address": "35 A1 valencia", "weight": "4", "points": "80"},
            {"date": "15.04.25", "address": "275 b valencia", "weight": "2.4", "points": "48"},
            {"date": "15.04.25", "address": "95e valencia", "weight": "3.5", "points": "70"},
            {"date": "15.04.25", "address": "18 e valencia", "weight": "3", "points": "60"},
            {"date": "15.04.25", "address": "86A1 valencia", "weight": "3.2", "points": "64"},
            {"date": "15.04.25", "address": "35 A valencia", "weight": "2.5", "points": "50"},
            {"date": "15.04.25", "address": "68A3 valencia", "weight": "2.6", "points": "52"},
            {"date": "19.04.25", "address": "95 e valencia", "weight": "1.8", "points": "36"},
            {"date": "22.04.25", "address": "266 e valencia", "weight": "3", "points": "60"},
            {"date": "22.04.25", "address": "166 a valencia", "weight": "2.2", "points": "44"},
            {"date": "25.04.25", "address": "36c1 valencia", "weight": "3", "points": "60"},
            {"date": "25.04.25", "address": "46c1 valencia", "weight": "3", "points": "60"},
            {"date": "25.4.25", "address": "266e valencia", "weight": "2.4", "points": "48"},
            {"date": "25.04.25", "address": "68A3 valencia", "weight": "3.3", "points": "66"},
            {"date": "29.04.25", "address": "276b valencia", "weight": "6", "points": "120"},
            {"date": "29.04.25", "address": "80 e valencia", "weight": "8", "points": "160"},
            {"date": "03.02.25", "address": "80 e valencia", "weight": "5", "points": "96"},
            {"date": "05.02.25", "address": "98 c valencia", "weight": "01.07.25", "points": "34"},
            {"date": "05.02.25", "address": "41 c1 valencia", "weight": "2.5", "points": "50"},
            {"date": "05.02.25", "address": "23 f valencia", "weight": "2", "points": "40"},
            {"date": "05.02.25", "address": "95 e valencia", "weight": "", "points": "1000 points given left 39"},
            {"date": "07.02.25", "address": "27 A1 valencia", "weight": "4.2", "points": "84"},
            {"date": "07.02.25", "address": "182 A1 valencia", "weight": "2.2", "points": "44"},
            {"date": "10.02.25", "address": "98 c valencia", "weight": "2.4", "points": "48"},
            {"date": "10.02.25", "address": "172 c valencia", "weight": "3.3", "points": "66"},
            {"date": "10.02.25", "address": "108 a2 valencia", "weight": "1.5", "points": "30"},
            {"date": "10.02.28", "address": "35 A1 valencia", "weight": "2.2", "points": "44"},
            {"date": "10.02.25", "address": "27 A1 valencia", "weight": "", "points": "1000 points given"},
            {"date": "12.02.25", "address": "124 j block valencia", "weight": "3.5", "points": "70"},
            {"date": "12.02.25", "address": "125 c valencia", "weight": "3.2", "points": "63"},
            {"date": "12.02.25", "address": "87 c valencia", "weight": "2.8", "points": "56"},
            {"date": "12.02.25", "address": "36 c1 Valencia", "weight": "2.5", "points": "50"},
            {"date": "12.02.25", "address": "95 e valencia", "weight": "6.2", "points": "124"},
            {"date": "14.02.25", "address": "40 j valencia", "weight": "2.5", "points": "50"},
            {"date": "14.02.25", "address": "276 b valencia", "weight": "3.2", "points": "64"},
            {"date": "14.02.25", "address": "41 c1 Valencia", "weight": "3.4", "points": "68"},
            {"date": "17.02.25", "address": "98 c valencia", "weight": "3.2", "points": "64"},
            {"date": "17.02.25", "address": "80e valencia", "weight": "2.2", "points": "44"},
            {"date": "17.02.25", "address": "80 e valencia", "weight": "6.1", "points": "122"},
            {"date": "17.02.25", "address": "102 e1 valencia", "weight": "2.4", "points": "48"},
            {"date": "17.02.25", "address": "74 A1 valencia", "weight": "3.8", "points": "76"},
            {"date": "20.02.25", "address": "98 c valencia", "weight": "4.1", "points": "82"},
            {"date": "20.02.25", "address": "78 c valencia", "weight": "2.8", "points": "56"},
            {"date": "20.02.25", "address": "120 c valencia", "weight": "2.4", "points": "48"},
            {"date": "20.02.25", "address": "132 e1 valencia", "weight": "2.6", "points": "52"},
            {"date": "25.02.25", "address": "36 c 1 Valencia", "weight": "2", "points": "40"},
            {"date": "25.02.25", "address": "41 c 11 varancia", "weight": "4.1", "points": "82"},
            {"date": "25.02.25", "address": "119 e block varancia", "weight": "3.2", "points": "64"},
            {"date": "25.02/25", "address": "266 e block Valencia", "weight": "2.5", "points": "50"},
            {"date": "25.02/25", "address": "84 f block Valencia", "weight": "4.1", "points": "82"},
            {"date": "25. 02. 25", "address": "98 c block valencia", "weight": "3.1", "points": "62"},
            {"date": "16.01.25", "address": "106 j block valencia", "weight": "3.2", "points": "64"},
            {"date": "21.01.25", "address": "21 e valencia", "weight": "5.6", "points": "112"},
            {"date": "21.01.25", "address": "111 e valencia", "weight": "3.4", "points": "68"},
            {"date": "21 01.25", "address": "266 e valencia", "weight": "2.8", "points": "56"},
            {"date": "21.01.25", "address": "95 e valencia", "weight": "2.5", "points": "50"},
            {"date": "21.01.25", "address": "80 e valencia", "weight": "2.5", "points": "50"},
            {"date": "27.01.25", "address": "33 c1 valencia", "weight": "1", "points": "20"},
            {"date": "29.01.25", "address": "41 c1 Valencia", "weight": "4.2", "points": "84"},
            {"date": "29.01.25", "address": "98c valencia", "weight": "3.1", "points": "62"},
            {"date": "29.01.25", "address": "84 f valencia", "weight": "2.6", "points": "52"},
            {"date": "29.01.25", "address": "95e valencia", "weight": "4.6", "points": "92"},
            {"date": "29.01.25", "address": "216 A1 valencia", "weight": "5.8", "points": "116"},
            {"date": "29.01.25", "address": "202 A1 valencia", "weight": "2.8", "points": "56"},
        ]
        
        all_collection_data = collection_data_2024 + collection_data_2025
        
        # Get all Valencia users
        valencia_users = CustomUser.objects.filter(location__icontains='valencia')
        
        for user in valencia_users:
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
        {"date": "12/02/2024", "address": "14 A3 valencia", "weight": "2.4", "points": "48"},
        {"date": "12/03/2024", "address": "71 M valencia", "weight": "2.2", "points": "44"},
        {"date": "12/03/2024", "address": "182 A1 valencia", "weight": "3.2", "points": "64"},
        {"date": "12/03/2024", "address": "27 A1 valencia", "weight": "5.5", "points": "110"},
        {"date": "12/03/2024", "address": "266/A E valencia", "weight": "4.2", "points": "84"},
        {"date": "12/03/2024", "address": "4 L valencia", "weight": "4.7", "points": "94"},
        {"date": "12/04/2024", "address": "111 E valencia", "weight": "4", "points": "80"},
        {"date": "12/04/2024", "address": "95 E valencia", "weight": "4.4", "points": "88"},
        {"date": "12/04/2024", "address": "98 C block valencia", "weight": "2.6", "points": "53"},
        {"date": "12/05/2024", "address": "276 B valencia", "weight": "3.8", "points": "80"},
    ],
    "collection_data_2025": [
        {"date": "02.05.25", "address": "18 e valencia", "weight": "3.2", "points": "64"},
        {"date": "02.05.25", "address": "45j valencia", "weight": "3.3", "points": "66"},
        {"date": "05.05.25", "address": "95e valencia", "weight": "6", "points": "120"},
        {"date": "12.05.25", "address": "36 c1 valencia3.6", "weight": "3.6", "points": "72"},
        {"date": "12.05.25", "address": "98c valencia", "weight": "2.5", "points": "50"},
        {"date": "12.05.25", "address": "95 e valencia", "weight": "4", "points": "80"},
        {"date": "12.05.25", "address": "84 e valencia", "weight": "4.5+6", "points": "90+120"},
        {"date": "12.05.25", "address": "18e valencia", "weight": "3", "points": "60"},
    ],
    "total_collections": 18,
    "generated_at": "2024-12-19T10:30:00.000Z"
}