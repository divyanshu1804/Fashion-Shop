from app import app, db, init_db
import os
import socket

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
            print("Initializing database...")
            db.create_all()
            init_db()
        else:
            print("Database already exists. Skipping initialization.")
    
    # Get the local IP address
    local_ip = get_local_ip()
    port = 5000
    
    print(f"\n{'='*50}")
    print(f"Fashion Store E-commerce Server")
    print(f"{'='*50}")
    print(f"Local URL: http://127.0.0.1:{port}")
    print(f"Network URL: http://{local_ip}:{port}")
    print(f"{'='*50}")
    print("Press Ctrl+C to stop the server")
    print(f"{'='*50}\n")
    
    # Run the application
    app.run(debug=False, host='0.0.0.0', port=port) 