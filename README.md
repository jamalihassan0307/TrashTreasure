# Recycle Bin 🗑️➡️💎

A modern, eco-friendly Django web application that transforms waste collection into a rewarding experience. Users can submit trash for collection, riders can manage pickups, and admins can oversee the entire operation.

## ✨ Features

### 🌟 User Experience
- **Beautiful, Modern UI** with Bootstrap 5 and custom CSS
- **Responsive Design** that works on all devices
- **Real-time Status Tracking** for trash collections
- **Reward Points System** for completed collections
- **Image Upload** for trash verification

### 👥 User Types & Panels

#### 1. **Regular Users** 👤
- Submit trash collection requests
- Track collection progress in real-time
- View collection history and earned points
- Manage profile information

#### 2. **Riders** 🚗
- View assigned collections
- Update collection status (On Way, Arrived, Picked Up)
- Complete collections with details and photos
- Award points to users

#### 3. **Admins** ⚙️
- Monitor system performance
- Assign riders to collections
- Verify completed collections
- Manage users and operations

### 🔄 Collection Workflow
1. **User Submission** → Photo + Description + Location
2. **Admin Assignment** → Assign to available rider
3. **Rider Collection** → Status updates throughout process
4. **Completion** → Points awarded, collection verified
5. **Verification** → Admin review and approval

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Django 5.1.7
- Pillow (for image handling)

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd TrashToTreasure

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

### Default Admin Credentials
- **Username**: admin
- **Password**: admin123
- **User Type**: Admin

## 🏗️ Project Structure

```
TrashToTreasure/
├── accounts/                 # User management app
│   ├── models.py            # CustomUser and ActivityLog models
│   ├── views.py             # Profile management views
│   └── urls.py              # Account-related URLs
├── trash/                   # Core trash management app
│   ├── models.py            # TrashSubmission, CollectionRecord models
│   ├── views.py             # Trash submission and collection views
│   └── urls.py              # Trash-related URLs
├── dashboard/               # Main dashboard app
│   ├── views.py             # Dashboard views for all user types
│   └── urls.py              # Dashboard URLs
├── static/                  # Static files
│   └── style.css            # Custom CSS with eco-friendly theme
├── templates/               # HTML templates
│   ├── base.html            # Base template with navigation
│   ├── dashboard/           # Dashboard templates
│   ├── trash/               # Trash management templates
│   └── accounts/            # User profile templates
├── media/                   # User-uploaded files
│   ├── profile_images/      # User profile pictures
│   ├── trash_images/        # Trash submission photos
│   ├── id_proofs/          # Rider ID verification
│   └── collection_images/   # Collection completion photos
└── manage.py                # Django management script
```

## 🎨 UI/UX Features

### Design Philosophy
- **Eco-Friendly Theme** with green color scheme
- **Modern Card-based Layout** for easy navigation
- **Interactive Elements** with hover effects and animations
- **Responsive Grid System** for all screen sizes
- **Icon Integration** with Font Awesome

### Key UI Components
- **Hero Section** with compelling call-to-action
- **Statistics Cards** showing key metrics
- **Progress Timeline** for collection tracking
- **Modal Forms** for quick actions
- **Status Badges** with color coding
- **Data Tables** with sorting and filtering

## 🔐 Security Features

- **CSRF Protection** on all forms
- **User Authentication** with custom user model
- **Role-based Access Control** for different user types
- **File Upload Validation** for images
- **Secure Password Management**

## 📱 Responsive Design

- **Mobile-First Approach** with Bootstrap 5
- **Touch-Friendly Interface** for mobile devices
- **Adaptive Layouts** for tablets and desktops
- **Optimized Images** for fast loading

## 🚀 Deployment

### Production Settings
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
STATIC_ROOT = '/path/to/static/'
MEDIA_ROOT = '/path/to/media/'
```

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django Framework for the robust web framework
- Bootstrap 5 for the responsive UI components
- Font Awesome for the beautiful icons
- The open-source community for inspiration

## 📞 Support

For support and questions:
- Email: recyclebin.pakistan@gmail.com
- Documentation: [Link to docs]
- Issues: https://github.com/jamalihassan0307/TrashToTreasure/issues

---

**Made with ❤️ for a cleaner, greener world! 🌍♻️**
