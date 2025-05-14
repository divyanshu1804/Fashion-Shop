from flask import Flask, render_template, url_for, request, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta
import json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import time
import random
import string

# Configure upload folder
UPLOAD_FOLDER = 'static/images/profile'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Currency conversion rate (1 USD to INR)
USD_TO_INR_RATE = 83.12  # As of March 2025 (example rate)

# Helper function to convert USD to INR
def usd_to_inr(usd_amount):
    # Convert to INR and round to nearest integer
    return round(usd_amount * USD_TO_INR_RATE)

@app.context_processor
def utility_processor():
    return dict(usd_to_inr=usd_to_inr)

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    profile_image = db.Column(db.String(200), default='images/profile/default-profile.jpg')
    phone = db.Column(db.String(20), unique=True, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Address fields
    street_address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='India')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_full_address(self):
        address_parts = []
        if self.street_address:
            address_parts.append(self.street_address)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        
        if address_parts:
            return ", ".join(address_parts)
        return "No address provided"

# OTP Model for phone verification
class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    is_verified = db.Column(db.Boolean, default=False)
    
    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create_otp_for_phone(phone):
        # Delete any existing OTPs for this phone
        OTP.query.filter_by(phone=phone).delete()
        db.session.commit()
        
        # Create new OTP
        otp_code = OTP.generate_otp()
        otp = OTP(phone=phone, otp_code=otp_code)
        db.session.add(otp)
        db.session.commit()
        return otp_code
    
    @staticmethod
    def verify_otp(phone, otp_code):
        otp = OTP.query.filter_by(
            phone=phone, 
            otp_code=otp_code, 
            is_verified=False
        ).first()
        
        if not otp:
            return False
        
        if otp.expires_at < datetime.utcnow():
            return False
        
        otp.is_verified = True
        db.session.commit()
        return True

# Product Model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

# Order Model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    order_total = db.Column(db.Float, nullable=False)
    order_items = db.Column(db.Text, nullable=False)  # JSON string of items
    
    user = db.relationship('User', backref=db.backref('orders', lazy=True))

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type', 'username')
        
        if login_type == 'username':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password', 'danger')
        
        elif login_type == 'phone':
            phone = request.form.get('phone')
            otp = request.form.get('otp')
            
            if OTP.verify_otp(phone, otp):
                user = User.query.filter_by(phone=phone).first()
                if user:
                    session['user_id'] = user.id
                    session['username'] = user.username
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('No account found with this phone number', 'danger')
            else:
                flash('Invalid OTP', 'danger')
    
    return render_template('login.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    # This is a placeholder route for sending OTP
    phone = request.form.get('phone')
    
    if not phone:
        return jsonify({'success': False, 'message': 'Phone number is required'})
    
    # Check if user exists with this phone
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'success': False, 'message': 'No account found with this phone number'})
    
    # Generate OTP
    otp_code = OTP.create_otp_for_phone(phone)
    
    # In a real application, you would send the OTP via SMS here
    # For demo purposes, we'll just return it in the response
    return jsonify({
        'success': True, 
        'message': f'OTP sent to {phone}',
        'otp': otp_code  # Remove this in production!
    })

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        
        # Validate form data
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('signup.html')
        
        # Check if phone already exists (if provided)
        if phone and User.query.filter_by(phone=phone).first():
            flash('Phone number already exists', 'danger')
            return render_template('signup.html')
        
        # Create new user
        user = User(
            username=username, 
            email=email, 
            first_name=first_name, 
            last_name=last_name,
            phone=phone
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please login to access your profile', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Update user profile
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.street_address = request.form.get('street_address')
        user.city = request.form.get('city')
        user.state = request.form.get('state')
        user.postal_code = request.form.get('postal_code')
        user.country = request.form.get('country')
        
        # Handle profile image upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create a unique filename
                unique_filename = f"{user.id}_{int(time.time())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profile', unique_filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                file.save(file_path)
                user.profile_image = f"images/profile/{unique_filename}"
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/')
def home():
    # Get featured products (for simplicity, just get the first 8 products)
    featured_products = Product.query.limit(8).all()
    return render_template('index.html', featured_products=featured_products)

@app.route('/reset_db')
def reset_db():
    db.drop_all()
    db.create_all()
    init_db()
    return redirect(url_for('home'))

def init_db():
    # Create sample products
    products = [
        {
            'name': 'Classic T-Shirt',
            'price': 19.99,
            'description': 'A comfortable and stylish t-shirt for everyday wear.',
            'category': 'men',
            'image_url': 'images/men/tshirt1.jpg'
        },
        {
            'name': 'Slim Fit Jeans',
            'price': 49.99,
            'description': 'Modern slim fit jeans that look great with any outfit.',
            'category': 'men',
            'image_url': 'images/men/jeans1.jpg'
        },
        {
            'name': 'Floral Dress',
            'price': 59.99,
            'description': 'Beautiful floral dress perfect for summer days.',
            'category': 'women',
            'image_url': 'images/women/dress1.jpg'
        },
        {
            'name': 'Casual Blouse',
            'price': 29.99,
            'description': 'Elegant blouse that can be dressed up or down.',
            'category': 'women',
            'image_url': 'images/women/blouse1.jpg'
        }
    ]
    
    for product_data in products:
        product = Product(**product_data)
        db.session.add(product)
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    db.session.commit()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ecommerce.db')
    initialize_db = not os.path.exists(db_path)
    
    with app.app_context():
        if initialize_db:
            print("Initializing database...")
            db.create_all()
            init_db()
        else:
            print("Database already exists. Skipping initialization.")
    
    app.run(debug=True) 