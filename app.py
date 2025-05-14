from flask import Flask, render_template, url_for, request, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta
import json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import time
import uuid
import random
import string
from sqlalchemy import inspect

# Configure upload folder
UPLOAD_FOLDER = 'static/images/profile'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'fashion_store_secret_key'  # Required for session management
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Currency conversion rate (1 USD to INR)
USD_TO_INR_RATE = 83.12  # As of March 2025 (example rate)

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # No longer nullable
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    profile_image = db.Column(db.String(200), default='images/profile/default-profile.jpg')
    phone = db.Column(db.String(20), nullable=True)  # Added phone field
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
    customer_phone = db.Column(db.String(20), nullable=False)  # Added phone field
    customer_address = db.Column(db.Text, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    order_total = db.Column(db.Float, nullable=False)
    order_items = db.Column(db.Text, nullable=False)  # JSON string of items
    
    user = db.relationship('User', backref=db.backref('orders', lazy=True))

# Helper function to convert USD to INR
def usd_to_inr(usd_amount):
    # Convert to INR and round to nearest integer
    return int(round(usd_amount * USD_TO_INR_RATE))

# Make the conversion function available to all templates
@app.context_processor
def utility_processor():
    return dict(usd_to_inr=usd_to_inr)

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
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
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        signup_type = request.form.get('signup_type', 'regular')
        
        if signup_type == 'regular':
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
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found. Please login again.', 'danger')
            session.pop('user_id', None)
            session.pop('username', None)
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            # Update user profile
            user.first_name = request.form.get('first_name', '')
            user.last_name = request.form.get('last_name', '')
            user.phone = request.form.get('phone', '')
            user.street_address = request.form.get('street_address', '')
            user.city = request.form.get('city', '')
            user.state = request.form.get('state', '')
            user.postal_code = request.form.get('postal_code', '')
            user.country = request.form.get('country', 'India')
            
            # Handle profile image upload
            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        try:
                            filename = secure_filename(file.filename)
                            # Create a unique filename
                            unique_filename = f"{user.id}_{int(time.time())}_{filename}"
                            
                            # Ensure directory exists
                            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                            
                            # Save the file
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                            file.save(file_path)
                            
                            # Update the user's profile image path
                            user.profile_image = f"images/profile/{unique_filename}"
                        except Exception as e:
                            flash(f'Error uploading image: {str(e)}', 'danger')
                            return redirect(url_for('profile'))
                    else:
                        flash('Invalid file type. Only images (png, jpg, jpeg, gif) are allowed.', 'danger')
                        return redirect(url_for('profile'))
            
            try:
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'danger')
            
            return redirect(url_for('profile'))
        
        # Get user's orders for the order history section
        try:
            orders = Order.query.filter_by(user_id=user.id).order_by(Order.order_date.desc()).all()
        except Exception as e:
            flash(f'Error retrieving orders: {str(e)}', 'danger')
            # Try to fix the database schema
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "order" ADD COLUMN customer_phone VARCHAR(20)'))
                    conn.commit()
                flash('Database schema updated. Please try again.', 'info')
                orders = []
            except:
                flash('Could not update database schema. Please contact support.', 'danger')
                orders = []
        
        return render_template('profile.html', user=user, orders=orders)
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route('/my-orders')
def my_orders():
    if 'user_id' not in session:
        flash('Please login to view your orders', 'warning')
        return redirect(url_for('login'))
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found. Please login again.', 'danger')
            session.pop('user_id', None)
            session.pop('username', None)
            return redirect(url_for('login'))
        
        # Get user's orders with most recent first
        try:
            orders = Order.query.filter_by(user_id=user.id).order_by(Order.order_date.desc()).all()
        except Exception as e:
            flash(f'Error retrieving orders: {str(e)}', 'danger')
            # Try to fix the database schema
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "order" ADD COLUMN customer_phone VARCHAR(20)'))
                    conn.commit()
                flash('Database schema updated. Please try again.', 'info')
            except:
                flash('Could not update database schema. Please contact support.', 'danger')
            return redirect(url_for('profile'))
        
        return render_template('my_orders.html', orders=orders, user=user)
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route('/my-order/<int:order_id>')
def my_order_detail(order_id):
    if 'user_id' not in session:
        flash('Please login to view your order', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Ensure the order exists
        order = Order.query.get_or_404(order_id)
        
        # Ensure the order belongs to the logged-in user
        if order.user_id != session['user_id']:
            flash('You do not have permission to view this order', 'danger')
            return redirect(url_for('my_orders'))
        
        try:
            order_items = json.loads(order.order_items)
        except json.JSONDecodeError:
            flash('Error loading order details. Please contact support.', 'danger')
            return redirect(url_for('my_orders'))
        
        return render_template('my_order_detail.html', order=order, order_items=order_items)
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('my_orders'))

# Routes
@app.route('/')
def home():
    products = Product.query.all()
    for product in products:
        print(f"Product: {product.name}, Image URL: {product.image_url}")
    return render_template('index.html', products=products)

@app.route('/category/<string:category>')
def category(category):
    products = Product.query.filter_by(category=category).all()
    print(f"Category: {category}, Number of products: {len(products)}")
    for product in products:
        print(f"Product: {product.name}, Category: {product.category}, Image URL: {product.image_url}")
    return render_template('category.html', products=products, category=category)

# Cart functionality
@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = product.price * quantity
            cart_items.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'image_url': product.image_url,
                'category': product.category,
                'item_total': item_total
            })
            total += item_total
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    cart = session.get('cart', {})
    cart_product_id = str(product_id)
    
    if cart_product_id in cart:
        cart[cart_product_id] += quantity
    else:
        cart[cart_product_id] = quantity
    
    session['cart'] = cart
    flash(f'{product.name} added to cart!', 'success')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True, 
            'cart_count': sum(cart.values()),
            'product_name': product.name,
            'product_price': usd_to_inr(product.price),
            'product_category': product.category
        })
    
    return redirect(request.referrer or url_for('home'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = session.get('cart', {})
    cart_product_id = str(product_id)
    quantity = int(request.form.get('quantity', 0))
    
    if quantity > 0:
        cart[cart_product_id] = quantity
    else:
        if cart_product_id in cart:
            del cart[cart_product_id]
    
    session['cart'] = cart
    flash('Cart updated successfully!', 'success')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': sum(cart.values())})
    
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart_product_id = str(product_id)
    
    if cart_product_id in cart:
        del cart[cart_product_id]
        session['cart'] = cart
        flash('Item removed from cart!', 'success')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': sum(cart.values())})
    
    return redirect(url_for('view_cart'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    flash('Your cart has been cleared!', 'success')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    
    if not cart:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Process the order
        cart_items = []
        total = 0
        
        for product_id, quantity in cart.items():
            product = Product.query.get(product_id)
            if product:
                item_total = product.price * quantity
                cart_items.append({
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'quantity': quantity,
                    'item_total': item_total
                })
                total += item_total
        
        # Create new order
        order = Order(
            customer_name=request.form.get('name'),
            customer_email=request.form.get('email'),
            customer_phone=request.form.get('phone'),
            customer_address=f"{request.form.get('street_address')}, {request.form.get('city')}, {request.form.get('state')}, {request.form.get('postal_code')}, {request.form.get('country')}",
            order_total=total,
            order_items=json.dumps(cart_items)
        )
        
        # Associate order with user if logged in
        if 'user_id' in session:
            order.user_id = session['user_id']
        
        db.session.add(order)
        db.session.commit()
        
        # Clear the cart
        session.pop('cart', None)
        
        flash('Your order has been placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    # GET request - show checkout form
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = product.price * quantity
            cart_items.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'image_url': product.image_url,
                'category': product.category,
                'item_total': item_total
            })
            total += item_total
    
    # Pre-fill form with user data if logged in
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    
    return render_template('checkout.html', cart_items=cart_items, total=total, user=user)

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    order_items = json.loads(order.order_items)
    
    return render_template('order_confirmation.html', order=order, order_items=order_items)

@app.route('/admin/orders')
def admin_orders():
    # Simple admin authentication
    if 'user_id' not in session:
        flash('Please login to access admin panel', 'warning')
        return redirect(url_for('login'))
    
    # Check if user is admin (check for username 'admin' instead of user_id 1)
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('home'))
    
    # Get all orders with most recent first
    orders = Order.query.order_by(Order.order_date.desc()).all()
    
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/users')
def admin_users():
    # Simple admin authentication
    if 'user_id' not in session:
        flash('Please login to access admin panel', 'warning')
        return redirect(url_for('login'))
    
    # Check if user is admin (check for username 'admin' instead of user_id 1)
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('home'))
    
    # Get all users
    users = User.query.all()
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/order/<int:order_id>')
def admin_order_detail(order_id):
    # Simple admin authentication
    if 'user_id' not in session:
        flash('Please login to access admin panel', 'warning')
        return redirect(url_for('login'))
    
    # Check if user is admin (check for username 'admin' instead of user_id 1)
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    order_items = json.loads(order.order_items)
    
    return render_template('admin_order_detail.html', order=order, order_items=order_items)

@app.route('/reset_db')
def reset_db():
    db.drop_all()
    db.create_all()
    init_db()
    return redirect(url_for('home'))

def init_db():
    db.create_all()
    # Check if products exist
    if not Product.query.first():
        products = [
            {
                'name': 'Men\'s Classic T-Shirt',
                'price': 29.99,
                'description': 'Comfortable cotton t-shirt for everyday wear',
                'category': 'men',
                'image_url': 'static/images/men/pexels-chetanvlad-1766702.jpg'
            },
            {
                'name': 'Men\'s Denim Jeans',
                'price': 79.99,
                'description': 'Classic fit denim jeans',
                'category': 'men',
                'image_url': 'static/images/men/pexels-hazardos-1306248.jpg'
            },
            {
                'name': 'Men\'s Casual Outfit',
                'price': 89.99,
                'description': 'Stylish casual outfit for any occasion',
                'category': 'men',
                'image_url': 'static/images/men/pexels-chloekalaartist-1043474.jpg'
            },
            {
                'name': 'Men\'s Formal Shirt',
                'price': 69.99,
                'description': 'Cotton formal shirt for business wear',
                'category': 'men',
                'image_url': 'static/images/men/pexels-ajaykumar786-1337477.jpg'
            },
            {
                'name': 'Men\'s Street Style',
                'price': 129.99,
                'description': 'Modern street style ensemble',
                'category': 'men',
                'image_url': 'static/images/men/pexels-thelazyartist-1342609.jpg'
            },
            {
                'name': 'Women\'s Summer Dress',
                'price': 59.99,
                'description': 'Elegant floral summer dress',
                'category': 'women',
                'image_url': 'static/images/women/pexels-chloekalaartist-1004642.jpg'
            },
            {
                'name': 'Women\'s Casual Outfit',
                'price': 89.99,
                'description': 'Stylish casual ensemble',
                'category': 'women',
                'image_url': 'static/images/women/pexels-luiz-gustavo-miertschink-925274-1877736.jpg'
            },
            {
                'name': 'Women\'s Fashion Collection',
                'price': 149.99,
                'description': 'Trendy fashion collection',
                'category': 'women',
                'image_url': 'static/images/women/pexels-leonnebrito-1844012.jpg'
            },
            {
                'name': 'Women\'s Elegant Dress',
                'price': 119.99,
                'description': 'Elegant dress for special occasions',
                'category': 'women',
                'image_url': 'static/images/women/pexels-olenagoldman-1021693 - Copy.jpg'
            },
            {
                'name': 'Women\'s Street Style',
                'price': 79.99,
                'description': 'Modern street style outfit',
                'category': 'women',
                'image_url': 'static/images/women/pexels-gabiguerino-1839904.jpg'
            },
            {
                'name': 'Kids\' Casual T-Shirt',
                'price': 24.99,
                'description': 'Comfortable cotton t-shirt for kids',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-tshirt.jpg'
            },
            {
                'name': 'Kids\' Denim Jeans',
                'price': 39.99,
                'description': 'Durable denim jeans for active kids',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-jeans.jpg'
            },
            {
                'name': 'Kids\' Summer Outfit',
                'price': 49.99,
                'description': 'Colorful summer outfit for children',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-summer.jpg'
            },
            {
                'name': 'Kids\' School Uniform',
                'price': 59.99,
                'description': 'Smart and comfortable school uniform',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-uniform.jpg'
            },
            {
                'name': 'Kids\' Party Dress',
                'price': 44.99,
                'description': 'Elegant party dress for special occasions',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-party.jpg'
            },
            {
                'name': 'Kids\' Winter Jacket',
                'price': 64.99,
                'description': 'Warm and cozy winter jacket for cold days',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-winter.jpg'
            },
            {
                'name': 'Kids\' Sneakers',
                'price': 34.99,
                'description': 'Comfortable and stylish sneakers for active kids',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-shoes.jpg'
            },
            {
                'name': 'Kids\' Backpack',
                'price': 29.99,
                'description': 'Colorful backpack perfect for school or travel',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-backpack.jpg'
            },
            {
                'name': 'Kids\' Pajama Set',
                'price': 27.99,
                'description': 'Soft and comfortable pajama set for a good night\'s sleep',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-tshirt.jpg'
            },
            {
                'name': 'Kids\' Accessories Set',
                'price': 19.99,
                'description': 'Cute hair accessories set for little girls',
                'category': 'kids',
                'image_url': 'static/images/kids/kids-backpack.jpg'
            }
        ]
        for product_data in products:
            product = Product(**product_data)
            db.session.add(product)
        db.session.commit()

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/dashboard')
def admin_dashboard():
    # Simple admin authentication
    if 'user_id' not in session:
        flash('Please login to access admin panel', 'warning')
        return redirect(url_for('login'))
    
    # Check if user is admin (check for username 'admin' instead of user_id 1)
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('home'))
    
    # Get all users
    users = User.query.all()
    
    # Get all orders with most recent first
    orders = Order.query.order_by(Order.order_date.desc()).all()
    
    # Get all products
    products = Product.query.all()
    
    # Get recent orders (last 5)
    recent_orders = orders[:5] if orders else []
    
    # Get recent users (last 5)
    recent_users = sorted(users, key=lambda x: x.created_date, reverse=True)[:5] if users else []
    
    # Calculate total revenue
    total_revenue = sum(usd_to_inr(order.order_total) for order in orders) if orders else 0
    
    # Count products by category
    category_counts = {}
    for product in products:
        if product.category in category_counts:
            category_counts[product.category] += 1
        else:
            category_counts[product.category] = 1
    
    return render_template('admin_dashboard.html', 
                           users=users, 
                           orders=orders, 
                           products=products,
                           recent_orders=recent_orders,
                           recent_users=recent_users,
                           total_revenue=total_revenue,
                           category_counts=category_counts)

@app.route('/admin/products')
def admin_products():
    # Simple admin authentication
    if 'user_id' not in session:
        flash('Please login to access admin panel', 'warning')
        return redirect(url_for('login'))
    
    # Check if user is admin (check for username 'admin' instead of user_id 1)
    user = User.query.get(session['user_id'])
    if not user or user.username != 'admin':
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('home'))
    
    # Get filter parameters
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'name')
    
    # Base query
    query = Product.query
    
    # Apply category filter
    if category:
        query = query.filter_by(category=category)
    
    # Apply sorting
    if sort == 'price_low':
        query = query.order_by(Product.price)
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'newest':
        query = query.order_by(Product.created_date.desc())
    else:  # Default to name
        query = query.order_by(Product.name)
    
    # Get products
    products = query.all()
    
    return render_template('admin_products.html', products=products)

if __name__ == '__main__':
    with app.app_context():
        try:
            # Only create tables if they don't exist, don't drop existing data
            db.create_all()
            
            # Check if the customer_phone column exists in the Order table
            inspector = inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('order')]
            
            # If customer_phone column doesn't exist, add it
            if 'customer_phone' not in columns:
                print("Adding missing customer_phone column to Order table...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE "order" ADD COLUMN customer_phone VARCHAR(20)'))
                    conn.commit()
                print("Database schema updated successfully.")
                
                # Update existing orders with a default phone number
                print("Updating existing orders with default phone number...")
                orders = Order.query.all()
                for order in orders:
                    if not hasattr(order, 'customer_phone') or not order.customer_phone:
                        order.customer_phone = "Not provided"
                db.session.commit()
                print("Existing orders updated successfully.")
            
            # Initialize products only if none exist
            if not Product.query.first():
                init_db()
            else:
                print("Database already contains products. Skipping initialization.")
        except Exception as e:
            print(f"Error updating database schema: {str(e)}")
            print("Recreating database from scratch...")
            db.drop_all()
            db.create_all()
            init_db()
            print("Database recreated successfully.")
            
    # Run the app on port 3000
    print("\n=================================================")
    print("Access the website at: http://localhost:3000")
    print("Or from other devices on your network using your local IP address")
    print("=================================================\n")
    app.run(debug=True, host='0.0.0.0', port=3000) 
