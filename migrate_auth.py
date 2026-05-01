"""
Migration script to add User authentication to existing database.
Run this ONCE after updating models.py
"""
from app import app, db
from models import User, StudyPlan
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    
    # Check if User table exists
    if 'user' not in inspector.get_table_names():
        print("Creating User table...")
        db.create_all()
        
        # Create a default user for existing plans
        default_user = User(username='admin', email='admin@example.com')
        default_user.set_password('admin123')
        db.session.add(default_user)
        db.session.commit()
        print(f"Created default user: admin / admin123")
        
        # Update existing plans to belong to default user
        plans = StudyPlan.query.all()
        for plan in plans:
            plan.user_id = default_user.id
        db.session.commit()
        print(f"Migrated {len(plans)} existing plans to default user")
        print("\nMigration complete!")
        print("You can now login with: admin@example.com / admin123")
    else:
        print("User table already exists. No migration needed.")
