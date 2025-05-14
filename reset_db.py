from app import app, db, init_db

if __name__ == '__main__':
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Initializing database...")
        init_db()
        print("Database reset successfully.") 