from app import app, db
from sqlalchemy import Column, String

# Run this script to migrate the database schema
# It will add the phone field to the User model and customer_phone field to the Order model

def migrate_db():
    with app.app_context():
        # Add phone column to User table if it doesn't exist
        try:
            db.engine.execute('ALTER TABLE user ADD COLUMN phone VARCHAR(20)')
            print("Added phone column to User table")
        except Exception as e:
            print(f"Error adding phone column to User table: {e}")
        
        # Add customer_phone column to Order table if it doesn't exist
        try:
            db.engine.execute('ALTER TABLE "order" ADD COLUMN customer_phone VARCHAR(20)')
            print("Added customer_phone column to Order table")
            
            # Set default value for existing orders
            db.engine.execute('UPDATE "order" SET customer_phone = "Not provided" WHERE customer_phone IS NULL')
            print("Set default value for customer_phone in existing orders")
        except Exception as e:
            print(f"Error adding customer_phone column to Order table: {e}")
        
        print("Migration completed")

if __name__ == "__main__":
    migrate_db() 