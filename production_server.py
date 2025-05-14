from waitress import serve
from app import app, db, init_db
import os
import socket
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fashion-store")

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a socket connection to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"  # Fallback to localhost

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    db_path = os.path.join(os.path.dirname(__file__), 'ecommerce.db')
    initialize_db = not os.path.exists(db_path)
    
    with app.app_context():
        if initialize_db:
            logger.info("Initializing database...")
            db.create_all()
            init_db()
        else:
            logger.info("Database already exists. Skipping initialization.")
    
    # Get the local IP address
    local_ip = get_local_ip()
    port = 5000
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Fashion Store E-commerce Production Server")
    logger.info(f"{'='*50}")
    logger.info(f"Local URL: http://127.0.0.1:{port}")
    logger.info(f"Network URL: http://{local_ip}:{port}")
    logger.info(f"{'='*50}")
    logger.info("Press Ctrl+C to stop the server")
    logger.info(f"{'='*50}\n")
    
    # Run the application with Waitress
    serve(app, host='0.0.0.0', port=port, threads=4) 