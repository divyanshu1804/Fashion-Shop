# Fashion Store E-commerce

A modern e-commerce website for fashion products built with Flask.

## Features

- User authentication (signup, login, profile management)
- Product browsing by categories
- Shopping cart functionality
- Checkout process
- Order history
- Profile image upload
- Address management
- Responsive design

## Deployment Options

### Option 1: Development Server (For Testing Only)

```bash
python run_server.py
```

This will start the Flask development server on your local network.

### Option 2: Production Server with Waitress

```bash
python production_server.py
```

This uses Waitress, a production-ready WSGI server, to serve the application.

### Option 3: Windows Service (For Long-Term Deployment)

1. Install NSSM (Non-Sucking Service Manager):
   ```
   winget install nssm
   ```
   or download from https://nssm.cc/download

2. Run the installation script:
   ```
   install_service.bat
   ```

3. Start the service:
   ```
   nssm start FashionStore
   ```

### Option 4: Docker Deployment

1. Build and start the Docker container:
   ```
   docker-compose up -d
   ```

2. Stop the container:
   ```
   docker-compose down
   ```

## Accessing the Website

Once deployed, the website will be available at:

- Local access: http://127.0.0.1:5000
- Network access: http://YOUR_LOCAL_IP:5000 (e.g., http://192.168.1.100:5000)

## Database Management

The application uses SQLite for data storage. The database file is `ecommerce.db`.

- To reset the database: Delete the `ecommerce.db` file and restart the application.
- To backup the database: Copy the `ecommerce.db` file to a safe location.

## Configuration

- Currency conversion rate can be modified in `app.py` by changing the `USD_TO_INR_RATE` value.
- Static files (images, CSS, JS) are stored in the `static` directory.
- HTML templates are stored in the `templates` directory. 